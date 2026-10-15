import logging
import re
from functools import lru_cache
from urllib.parse import quote

import requests
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 10
# Wikimedia asks API clients to identify themselves.
HEADERS = {"User-Agent": "travel-agentic/0.1 (https://github.com/apurvarane25/travel-agentic)"}


class CityNotFound(ValueError):
    """The geocoder has no match for the city name."""


@lru_cache(maxsize=256)
def get_coordinates(city: str) -> tuple[float, float]:
    """Return (latitude, longitude) for a city. Raises CityNotFound if there's no match."""
    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en", "format": "json"},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    results = response.json().get("results")  # key is absent when nothing matches
    if not results:
        raise CityNotFound(f"City '{city}' not found")
    return results[0]["latitude"], results[0]["longitude"]


@tool(response_format="content_and_artifact")
def get_weather(city: str, start_date: str, end_date: str) -> tuple[str, dict]:
    """Get the daily weather forecast for a city.

    Args:
        city: City name, e.g. "Lisbon".
        start_date: First day of the trip, YYYY-MM-DD.
        end_date: Last day of the trip, YYYY-MM-DD.
    """
    try:
        lat, lon = get_coordinates(city)
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date,
                "end_date": end_date or start_date,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
                "timezone": "auto",
            },
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        daily = response.json()["daily"]
    except Exception:
        # Day 2 replaces this: raise, and let the retry/error middleware handle it.
        logger.exception("get_weather failed for %s", city)
        return "Weather data is unavailable.", {"status": "error", "message": "The weather service failed."}

    days = [
        {"day": d, "temp_max_c": hi, "temp_min_c": lo, "precipitation_mm": rain}
        for d, hi, lo, rain in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["precipitation_sum"],
        )
    ]
    # The model reads this text; the UI uses the artifact.
    text = "\n".join(
        f"{d['day']}: High {d['temp_max_c']}°C, Low {d['temp_min_c']}°C, Rain {d['precipitation_mm']}mm"
        for d in days
    )
    return text, {"status": "ok", "days": days}


@tool(response_format="content_and_artifact")
def get_attractions(city: str, weather: str) -> tuple[str, dict]:
    """Get tourist attractions in a city from Wikipedia.

    Args:
        city: City name, e.g. "Lisbon".
        weather: The weather summary returned by get_weather.
    """
    try:
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "titles": city,
                "prop": "extracts",
                "explaintext": 1,
                "redirects": 1,
                "format": "json",
            },
            headers=HEADERS,
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        page = next(iter(response.json()["query"]["pages"].values()))
    except Exception:
        logger.exception("get_attractions failed for %s", city)
        return "Attraction data is unavailable.", {"status": "error", "message": "Wikipedia couldn't be reached."}

    title = page.get("title", city)
    source_url = "https://en.wikipedia.org/wiki/" + quote(title.replace(" ", "_"))
    page_content = page.get("extract", "")

    # Extraction logic unchanged for now; Day 2 replaces it (it rarely matches).
    attractions_section = re.search(
        r'(?: Attractions|Tourist attractions|Point of interest)(.*?)(?=\n==\Z)',
        page_content,
        re.IGNORECASE | re.DOTALL,
    )
    attractions = []
    if attractions_section:
        attractions = re.findall(r'[•\-\*]\s*([^•\-\*\n]+)', attractions_section.group(1))
        attractions = [a.strip() for a in attractions if len(a.strip()) > 3][:10]

    if not attractions:
        return (
            f"No attractions found for {city}.",
            {"status": "unavailable", "source_url": source_url, "message": "No attractions list found on Wikipedia."},
        )

    emoji = "🌧️" if "rain" in weather.lower() else "☀️"
    return f"{emoji} {', '.join(attractions)}", {"status": "ok", "items": attractions, "source_url": source_url}