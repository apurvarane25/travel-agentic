import logging
from functools import lru_cache

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import BaseMessage, ToolMessage
from pydantic import BaseModel, ValidationError

from models import AttractionsSection, TravelPlan, TravelRequest, WeatherSection
from tools import get_attractions, get_weather

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful travel assistant. "
    "First call get_weather for the trip dates, then call get_attractions with that weather summary. "
    "Then recommend what to do each day based on the weather."
)


def build_agent(model="google_genai:gemini-3.5-flash-lite"):
    return create_agent(model=model, tools=[get_weather, get_attractions], system_prompt=SYSTEM_PROMPT)


@lru_cache(maxsize=1)
def get_agent():
    """Build the agent once, on first use, instead of on every request."""
    return build_agent()


def plan_trip(request: TravelRequest, agent=None) -> TravelPlan:
    agent = agent or get_agent()
    result = agent.invoke({
        "messages": [{
            "role": "user",
            "content": (
                f"I'm visiting {request.city} from {request.start_date} to {request.end_date}. "
                "What should I do based on the weather?"
            ),
        }]
    })
    messages = result["messages"]
    return TravelPlan(
        city=request.city,
        start_date=request.start_date,
        end_date=request.end_date,
        weather=_section(messages, "get_weather", WeatherSection),
        attractions=_section(messages, "get_attractions", AttractionsSection),
        recommendation=messages[-1].text,  # .text handles Gemini's list-of-blocks content
    )


def _section(messages: list[BaseMessage], tool_name: str, section_model: type[BaseModel]):
    """Build a response section from the tool's structured output, not from the model's prose."""
    calls = [m for m in messages if isinstance(m, ToolMessage) and m.name == tool_name]
    if not calls:
        return section_model(status="error", message="The agent didn't fetch this data.")
    last = calls[-1]
    if last.status == "error" or not last.artifact:
        return section_model(status="error", message="This data couldn't be loaded.")
    try:
        return section_model.model_validate(last.artifact)
    except ValidationError:
        logger.exception("Unexpected %s output", tool_name)
        return section_model(status="error", message="This data couldn't be loaded.")