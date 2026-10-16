"""API tests with a fake model and fake HTTP: no network calls, no API key needed."""
from datetime import date, timedelta

import pytest
import requests
from fastapi.testclient import TestClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

import agent
import main
import tools


def days_from_today(n: int) -> str:
    return (date.today() + timedelta(days=n)).isoformat()


# ---------- fake model ----------

class FakeModel(GenericFakeChatModel):
    """Replays scripted messages. bind_tools is a no-op so create_agent accepts it."""
    def bind_tools(self, tools, **kwargs):
        return self


class ExplodingModel(FakeModel):
    """Fails the test if the agent ever calls the model."""
    def _generate(self, *args, **kwargs):
        raise AssertionError("the model should not have been called")


def calls_both_tools() -> FakeModel:
    return FakeModel(messages=iter([
        AIMessage(content="", tool_calls=[
            {"name": "get_weather", "id": "w1", "args": {}},
            {"name": "get_attractions", "id": "a1", "args": {}},
        ]),
        # Gemini 3.x returns a list of content blocks, not a string
        AIMessage(content=[{"type": "text", "text": "Enjoy your trip.", "extras": {"signature": "x"}}]),
    ]))


def use_model(monkeypatch, model):
    monkeypatch.setattr(agent, "get_agent", lambda: agent.build_agent(model, retry_delay=0))


# ---------- fake HTTP ----------

class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload, self.status_code = payload, status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code), response=self)


LISBON = {"name": "Lisbon", "admin1": "Lisbon", "country": "Portugal", "latitude": 38.7, "longitude": -9.1}
SPRINGFIELD = {"name": "Springfield", "admin1": "Missouri", "country": "United States", "latitude": 37.2, "longitude": -93.3}
WIKI_EXTRACT = "Intro\n Attractions\n• Belém Tower\n• Jerónimos Monastery\n=="


def forecast_for(params):
    start, end = date.fromisoformat(params["start_date"]), date.fromisoformat(params["end_date"])
    days = [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]
    n = len(days)
    return FakeResponse({"daily": {"time": days, "temperature_2m_max": [20.0] * n,
                                   "temperature_2m_min": [12.0] * n, "precipitation_sum": [0.0] * n}})


class FakeAPIs:
    """Replaces requests.get. Tests override a service by assigning a new handler to it."""
    def __init__(self):
        self.calls = []
        self.geocoding = lambda params: FakeResponse({"results": [LISBON]})
        self.forecast = forecast_for
        self.wikipedia = lambda params: FakeResponse(
            {"query": {"pages": {"1": {"title": params["titles"], "extract": WIKI_EXTRACT}}}})

    def get(self, url, params=None, headers=None, timeout=None):
        for service in ("geocoding", "forecast", "wikipedia"):
            if service in url:
                self.calls.append((service, params))
                return getattr(self, service)(params)
        raise AssertionError(f"unexpected URL: {url}")

    def count(self, service):
        return sum(1 for s, _ in self.calls if s == service)


@pytest.fixture
def apis(monkeypatch):
    fake = FakeAPIs()
    monkeypatch.setattr(tools.requests, "get", fake.get)
    tools.resolve_place.cache_clear()
    return fake


@pytest.fixture
def client(monkeypatch, apis):
    use_model(monkeypatch, calls_both_tools())
    return TestClient(main.app)


def plan(client, city="Lisbon", start=5, end=6):
    return client.post("/api/travel-plan", json={
        "city": city, "start_date": days_from_today(start), "end_date": days_from_today(end)})


# ---------- happy path ----------

def test_happy_path(client, apis):
    r = plan(client)
    assert r.status_code == 200
    body = r.json()
    assert body["location"]["country"] == "Portugal"
    assert body["weather"]["status"] == "ok" and len(body["weather"]["days"]) == 2
    assert body["attractions"] == {"status": "ok", "items": ["Belém Tower", "Jerónimos Monastery"],
                                   "source_url": "https://en.wikipedia.org/wiki/Lisbon", "message": None}
    assert body["recommendation"] == "Enjoy your trip."


# ---------- retries and partial failure ----------

def test_transient_failure_is_retried(client, apis):
    attempts = []
    def flaky(params):
        attempts.append(1)
        if len(attempts) < 3:
            raise requests.Timeout("slow")
        return forecast_for(params)
    apis.forecast = flaky

    body = plan(client).json()
    assert body["weather"]["status"] == "ok"
    assert len(attempts) == 3


def test_weather_down_still_returns_attractions(client, apis):
    def down(params):
        raise requests.ConnectionError("down")
    apis.forecast = down

    r = plan(client)
    assert r.status_code == 200
    body = r.json()
    assert body["weather"]["status"] == "error"
    assert body["weather"]["message"] == "The weather service is unavailable right now."
    assert body["attractions"]["status"] == "ok"
    assert apis.count("forecast") == 3  # 1 attempt + 2 retries


@pytest.mark.parametrize("response, message", [
    (FakeResponse({}, status_code=404), "The weather service is unavailable right now."),
    (FakeResponse({"unexpected": "shape"}), "The weather service returned data we couldn't read."),
])
def test_permanent_failures_are_not_retried(client, apis, response, message):
    apis.forecast = lambda params: response
    body = plan(client).json()
    assert body["weather"] == {"status": "error", "days": [], "message": message}
    assert apis.count("forecast") == 1


# ---------- forecast window ----------

def test_dates_beyond_forecast_are_unavailable(client, apis):
    body = plan(client, start=30, end=31).json()
    assert body["weather"]["status"] == "unavailable"
    assert apis.count("forecast") == 0  # no request we know would fail


def test_trip_partly_beyond_forecast_is_clipped(client, apis):
    body = plan(client, start=12, end=18).json()
    assert body["weather"]["status"] == "ok"
    assert len(body["weather"]["days"]) == tools.FORECAST_DAYS_AHEAD - 12 + 1
    assert "only covers up to" in body["weather"]["message"]


# ---------- validation: rejected before any API or model call ----------

@pytest.mark.parametrize("payload", [
    {"city": "Lisbon", "start_date": days_from_today(-30)},                                  # past
    {"city": "Lisbon", "start_date": days_from_today(5), "end_date": days_from_today(3)},   # end before start
    {"city": "Lisbon", "start_date": days_from_today(1), "end_date": days_from_today(20)},  # longer than 14 days
    {"city": "", "start_date": days_from_today(5)},                                          # empty city
    {"city": "Lisbon", "start_date": "20-10-2026"},                                          # bad date format
])
def test_invalid_requests_are_rejected(monkeypatch, apis, payload):
    use_model(monkeypatch, ExplodingModel(messages=iter([])))
    r = TestClient(main.app).post("/api/travel-plan", json=payload)
    assert r.status_code == 422
    assert apis.calls == []


def test_unknown_city_is_rejected_without_model_call(monkeypatch, apis):
    apis.geocoding = lambda params: FakeResponse({"generationtime_ms": 0.1})  # no "results" key
    use_model(monkeypatch, ExplodingModel(messages=iter([])))
    r = plan(TestClient(main.app), city="Xyzzy")
    assert r.status_code == 422
    assert r.json()["detail"][0]["type"] == "city_not_found"


def test_geocoder_down_returns_503(client, apis):
    def down(params):
        raise requests.ConnectionError("down")
    apis.geocoding = down
    assert plan(client).status_code == 503


# ---------- place resolution ----------

def test_ambiguous_city_uses_region_for_wikipedia(client, apis):
    apis.geocoding = lambda params: FakeResponse({"results": [SPRINGFIELD]})
    body = plan(client, city="Springfield").json()
    assert body["location"]["region"] == "Missouri"
    assert [p["titles"] for s, p in apis.calls if s == "wikipedia"] == ["Springfield, Missouri"]
    assert body["attractions"]["source_url"] == "https://en.wikipedia.org/wiki/Springfield,_Missouri"


def test_disambiguation_pages_are_skipped(client, apis):
    apis.geocoding = lambda params: FakeResponse({"results": [SPRINGFIELD]})
    apis.wikipedia = lambda params: FakeResponse(
        {"query": {"pages": {"1": {"title": params["titles"], "pageprops": {"disambiguation": ""}}}}})
    body = plan(client, city="Springfield").json()
    assert body["attractions"]["status"] == "unavailable"


# ---------- failures that should be loud ----------

def test_bug_in_tool_returns_502(client, monkeypatch):
    def buggy(text):
        raise NameError("name 're' is not defined")  # the original attractions bug
    monkeypatch.setattr(tools, "_extract_attractions", buggy)
    assert plan(client).status_code == 502


def test_agent_skipping_tools_is_reported(monkeypatch, apis):
    use_model(monkeypatch, FakeModel(messages=iter([AIMessage(content="I'll just guess.")])))
    body = plan(TestClient(main.app)).json()
    assert body["weather"]["status"] == "error"
    assert body["weather"]["message"] == "The agent didn't fetch this data."