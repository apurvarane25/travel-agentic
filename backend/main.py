import logging

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from agent import plan_trip
from models import TravelPlan, TravelRequest
from tools import CityNotFound, get_coordinates

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Travel Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/travel-plan", response_model=TravelPlan)
def get_travel_plan(request: TravelRequest) -> TravelPlan:
    # Reject unknown cities before spending a model call.
    try:
        get_coordinates(request.city)
    except CityNotFound:
        raise HTTPException(
            status_code=422,
            detail=[{
                "type": "city_not_found",
                "loc": ["body", "city"],
                "msg": f"Couldn't find a city called '{request.city}'",
                "input": request.city,
            }],
        )
    except requests.RequestException:
        # Geocoder is down: carry on; the weather section will report the failure.
        logger.warning("Geocoding check failed for %s", request.city, exc_info=True)

    try:
        return plan_trip(request)
    except Exception:
        logger.exception("Agent run failed")  # full error goes to the server log, not the client
        raise HTTPException(status_code=502, detail="The travel agent failed. Please try again.")