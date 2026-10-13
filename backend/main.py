from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agent import get_travel_recommendation

# Initialize FastAPI app
app = FastAPI()

# Enable CORS (so React can call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model (what React will send)
class TravelRequest(BaseModel):
    city: str
    start_date: str
    end_date: str

# Define response model (what we'll send back)
class TravelResponse(BaseModel):
    recommendation: str = ""
    error: str = ""

# Health check endpoint
@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/travel-plan")
def get_travel_plan(request: TravelRequest):
    try:
        result = get_travel_recommendation(
            request.city,
            request.start_date,
            request.end_date
        )
        return TravelResponse(recommendation=result, error="")
    except Exception as e:
        return TravelResponse(recommendation="", error=str(e))

# Run with: uvicorn main:app --reload