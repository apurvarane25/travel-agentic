import logging
import time
from dataclasses import asdict
from functools import lru_cache

import requests
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import ToolErrorMiddleware, ToolRetryMiddleware
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from pydantic import BaseModel, ValidationError

from models import AttractionsSection, Location, TravelPlan, TravelRequest, WeatherSection
from tools import Place, TripContext, UpstreamDataError, get_attractions, get_weather, is_transient

load_dotenv()
logger = logging.getLogger(__name__)

DEFAULT_MODEL = "google_genai:gemini-3.5-flash-lite"

SYSTEM_PROMPT = """You are a travel assistant.
For every trip, call get_weather and get_attractions. They already know the city and dates, and you can call both at once.
Then recommend what to do each day based on the forecast.

Rules:
- Only state weather figures that get_weather returned.
- If a tool returns no data or an error, say so plainly.
- If you suggest places from your own knowledge rather than from get_attractions, say they are general suggestions."""

SERVICE_NAMES = {"get_weather": "The weather service", "get_attractions": "Wikipedia"}


def on_tool_error(exc: Exception, request) -> str | None:
    """Turn known failures into a message the model (and the UI) can show. Anything else propagates."""
    service = SERVICE_NAMES.get(request.tool_call["name"], "A data source")
    if isinstance(exc, requests.RequestException):
        logger.warning("%s failed after retries: %r", request.tool_call["name"], exc)
        return f"{service} is unavailable right now."
    if isinstance(exc, UpstreamDataError):
        logger.warning("%s returned unexpected data: %r", request.tool_call["name"], exc)
        return f"{service} returned data we couldn't read."
    return None  # unknown exception = a bug: let it fail loudly (502) instead of hiding it


def build_agent(model=DEFAULT_MODEL, retry_delay: float = 0.5):
    return create_agent(
        model=model,
        tools=[get_weather, get_attractions],
        system_prompt=SYSTEM_PROMPT,
        context_schema=TripContext,
        middleware=[
            # The first entry wraps all the others, so error handling sees an exception
            # only after the retry middleware below has given up.
            ToolErrorMiddleware(on_error=on_tool_error),
            ToolRetryMiddleware(
                max_retries=2,              # 3 attempts in total
                retry_on=is_transient,      # timeouts, connection errors, 429, 5xx
                on_failure="error",         # re-raise after the last attempt, so the outer middleware sees it
                initial_delay=retry_delay,  # 0.5 s, then 1 s
                max_delay=4.0,
            ),
        ],
    )


@lru_cache(maxsize=1)
def get_agent():
    """Build the agent once, on first use, instead of on every request."""
    return build_agent()


def plan_trip(request: TravelRequest, place: Place, agent=None) -> TravelPlan:
    agent = agent or get_agent()
    context = TripContext(place=place, start_date=request.start_date, end_date=request.end_date)
    started = time.perf_counter()
    result = agent.invoke(
        {"messages": [{
            "role": "user",
            "content": f"Plan my trip to {place.display_name} from {request.start_date} to {request.end_date}.",
        }]},
        context=context,
    )
    messages = result["messages"]
    model_calls = [m for m in messages if isinstance(m, AIMessage)]
    logger.info(
        "plan_trip city=%s took %.1fs: %d model calls, tools=%s",
        place.display_name,
        time.perf_counter() - started,
        len(model_calls),
        [tc["name"] for m in model_calls for tc in m.tool_calls],
    )
    return TravelPlan(
        city=request.city,
        location=Location(**asdict(place)),
        start_date=request.start_date,
        end_date=request.end_date,
        weather=_section(messages, "get_weather", WeatherSection),
        attractions=_section(messages, "get_attractions", AttractionsSection),
        recommendation=messages[-1].text,  # .text handles Gemini's list-of-blocks content
    )


def _section(messages: list[BaseMessage], tool_name: str, section_model: type[BaseModel]):
    """Build a response section from the tool's structured output, not from the model's prose."""
    call_ids = {
        tc["id"] for m in messages if isinstance(m, AIMessage) for tc in m.tool_calls if tc["name"] == tool_name
    }
    results = [m for m in messages if isinstance(m, ToolMessage) and m.tool_call_id in call_ids]
    if not results:
        return section_model(status="error", message="The agent didn't fetch this data.")
    last = results[-1]
    if last.status == "error":
        # Content comes from on_tool_error, so it's safe to show.
        return section_model(status="error", message=last.text or "This data couldn't be loaded.")
    if not last.artifact:
        return section_model(status="error", message="This data couldn't be loaded.")
    try:
        return section_model.model_validate(last.artifact)
    except ValidationError:
        logger.exception("Unexpected %s output", tool_name)
        return section_model(status="error", message="This data couldn't be loaded.")