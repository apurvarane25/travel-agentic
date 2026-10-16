import logging
import re
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from urllib.parse import quote

import requests
from langchain.tools import ToolRuntime, tool

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
WIKIPEDIA_URL = "https://en.wikipedia.org/w/api.php"

TIMEOUT = (3, 5)  # (connect, read) seconds; retries multiply this, so keep it short
FORECAST_DAYS_AHEAD = 14  # Open-Meteo forecasts 16 days; 2 days of margin for time zones
# Wikimedia asks API clients to identify themselves.
HEADERS = {"User-Agent": "travel-agentic/0.1 (https://github.com/apurvarane25/travel-agentic)"}


class CityNotFound(ValueError):
    """The geocoder has no match for the city name."""


class UpstreamDataError(Exception):
    """An upstream API answered, but not in the shape we expected. Retrying won't help."""


@dataclass(frozen=True)
class Place:
    name: str
    region: str | None
    country: str | None
    latitude: float
    longitude: float

    @property
    def display_name(self) -> str:
        parts = [self.name]
        if self.region and self.region != self.name:
            parts.append(self.region)
        if self.country:
            parts.append(self.country)
        return ", ".join(parts)


@dataclass(frozen=True)
class TripContext:
    """Per-request inputs the tools read directly. The model never sees or edits these."""
    place: Place
    start_date: date
    end_date: date


def is_transient(exc: Exception) -> bool:
    """Retry timeouts, dropped connections, rate limits and server errors; nothing else."""
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code == 429 or exc.response.status_code >= 500
    return False


def _get_json(url: str, params: dict, headers: dict | None = None) -> dict:
    response = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()  # 4xx/5xx -> requests.HTTPError
    return response.json()


@lru_cache(maxsize=256)
def resolve_place(city: str) -> Place:
    """Geocode a city name. Raises CityNotFound, or requests exceptions if the geocoder is down."""
    data = _get_json(GEOCODING_URL, {"name": city, "count": 1, "language": "en", "format": "json"})
    results = data.get("results")  # key is absent when nothing matches
    if not results:
        raise CityNotFound(f"City '{city}' not found")
    r = results[0]
    return Place(
        name=r["name"],
        region=r.get("admin1"),
        country=r.get("country"),
        latitude=r["latitude"],
        longitude=r["longitude"],
    )


@tool(response_format="content_and_artifact")
def get_weather(runtime: ToolRuntime[TripContext]) -> tuple[str, dict]:
    """Get the daily forecast (high, low, precipitation) for the trip's city and dates."""
    trip = runtime.context
    last_forecast_day = date.today() + timedelta(days=FORECAST_DAYS_AHEAD)
    if trip.start_date > last_forecast_day:
        message = f"Forecasts are only available up to {last_forecast_day.isoformat()}."
        return f"No forecast is available yet for these dates. {message}", {"status": "unavailable", "message": message}

    end = min(trip.end_date, last_forecast_day)
    # Network and HTTP errors propagate: the retry and error middleware handle them.
    data = _get_json(FORECAST_URL, {
        "latitude": trip.place.latitude,
        "longitude": trip.place.longitude,
        "start_date": trip.start_date.isoformat(),
        "end_date": end.isoformat(),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "auto",
    })
    try:
        daily = data["daily"]
        days = [
            {"day": d, "temp_max_c": hi, "temp_min_c": lo, "precipitation_mm": rain}
            for d, hi, lo, rain in zip(
                daily["time"],
                daily["temperature_2m_max"],
                daily["temperature_2m_min"],
                daily["precipitation_sum"],
            )
        ]
    except (KeyError, TypeError) as exc:
        raise UpstreamDataError("Unexpected forecast response") from exc

    message = f"The forecast only covers up to {end.isoformat()}." if end < trip.end_date else None
    # The model reads this text; the UI uses the artifact.
    text = "\n".join(
        f"{d['day']}: High {d['temp_max_c']}°C, Low {d['temp_min_c']}°C, Rain {d['precipitation_mm']}mm"
        for d in days
    )
    if message:
        text += f"\n{message}"
    return text, {"status": "ok", "days": days, "message": message}


def _wikipedia_titles(place: Place) -> list[str]:
    # Most specific first, so "Springfield" becomes "Springfield, Missouri", not the disambiguation page.
    titles = []
    if place.region and place.region != place.name:
        titles.append(f"{place.name}, {place.region}")
    titles.append(place.name)
    return titles


def _find_wikipedia_article(place: Place) -> dict | None:
    for title in _wikipedia_titles(place):
        data = _get_json(
            WIKIPEDIA_URL,
            {
                "action": "query",
                "titles": title,
                "prop": "extracts|pageprops",
                "ppprop": "disambiguation",
                "explaintext": 1,
                "redirects": 1,
                "format": "json",
            },
            headers=HEADERS,
        )
        try:
            page = next(iter(data["query"]["pages"].values()))
        except (KeyError, StopIteration, AttributeError) as exc:
            raise UpstreamDataError("Unexpected Wikipedia response") from exc
        if "missing" in page or "disambiguation" in page.get("pageprops", {}):
            continue
        return page
    return None


def _extract_attractions(page_content: str) -> list[str]:
    # Unchanged from the original; it rarely matches. Replaced in its own step.
    section = re.search(
        r'(?: Attractions|Tourist attractions|Point of interest)(.*?)(?=\n==\Z)',
        page_content,
        re.IGNORECASE | re.DOTALL,
    )
    if not section:
        return []
    items = re.findall(r'[•\-\*]\s*([^•\-\*\n]+)', section.group(1))
    return [a.strip() for a in items if len(a.strip()) > 3][:10]


@tool(response_format="content_and_artifact")
def get_attractions(runtime: ToolRuntime[TripContext]) -> tuple[str, dict]:
    """Get tourist attractions in the trip's city from its Wikipedia article."""
    place = runtime.context.place
    page = _find_wikipedia_article(place)
    if page is None:
        message = "No Wikipedia article found for this city."
        return f"{message} ({place.display_name})", {"status": "unavailable", "message": message}

    source_url = "https://en.wikipedia.org/wiki/" + quote(page["title"].replace(" ", "_"), safe=",()")
    attractions = _extract_attractions(page.get("extract", ""))
    if not attractions:
        message = "No attractions list found on Wikipedia."
        return message, {"status": "unavailable", "source_url": source_url, "message": message}
    return "Attractions: " + ", ".join(attractions), {"status": "ok", "items": attractions, "source_url": source_url}