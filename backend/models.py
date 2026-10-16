"""Request/response contract for POST /api/travel-plan.

Partial failures go in the body; whole-request failures use HTTP status codes.

| Situation                                 | HTTP | weather     | attractions |
|-------------------------------------------|------|-------------|-------------|
| Everything worked                         | 200  | ok          | ok          |
| Trip starts beyond the forecast window    | 200  | unavailable | ok          |
| No attractions found for the city         | 200  | ok          | unavailable |
| Weather API down (after retries)          | 200  | error       | ok          |
| Unknown city, invalid or past dates       | 422  | -           | -           |
| Model (Gemini) call failed                | 502  | -           | -           |
| Location service (geocoding) down         | 503  | -           | -           |
"""

from datetime import date, timedelta
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints, model_validator

MAX_TRIP_DAYS = 14

# ok          = data present
# unavailable = expected gap (e.g. dates beyond the forecast); retrying won't help
# error       = something broke upstream (timeout, 5xx); retrying later might help
Status = Literal["ok", "unavailable", "error"]


class TravelRequest(BaseModel):
    city: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    start_date: date
    end_date: date | None = None  # defaults to start_date (a one-day trip)

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date is None:
            self.end_date = self.start_date
        # One day of slack: the user's "today" can be the server's yesterday.
        if self.start_date < date.today() - timedelta(days=1):
            raise ValueError("start_date can't be in the past")
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if (self.end_date - self.start_date).days + 1 > MAX_TRIP_DAYS:
            raise ValueError(f"trips can be at most {MAX_TRIP_DAYS} days")
        return self


class Location(BaseModel):
    """The place the geocoder resolved the city name to."""
    name: str
    region: str | None = None
    country: str | None = None
    latitude: float
    longitude: float


class DailyWeather(BaseModel):
    day: date
    temp_max_c: float
    temp_min_c: float
    precipitation_mm: float


class WeatherSection(BaseModel):
    status: Status
    days: list[DailyWeather] = []
    message: str | None = None


class AttractionsSection(BaseModel):
    status: Status
    items: list[str] = []
    source_url: str | None = None
    message: str | None = None


class TravelPlan(BaseModel):
    city: str
    location: Location
    start_date: date
    end_date: date
    weather: WeatherSection
    attractions: AttractionsSection
    recommendation: str