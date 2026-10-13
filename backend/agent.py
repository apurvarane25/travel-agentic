from dotenv import load_dotenv
from tools import get_weather, get_attractions
from langchain.agents import create_agent
from langchain_core.tools import tool
import requests
import re

load_dotenv()

# Your tool functions here (get_coordinates, get_weather, get_attractions)

def get_travel_recommendation(city: str, start_date: str, end_date: str) -> str:
    """Get travel recommendation from agent"""
    try:
        # Create agent
        agent = create_agent(
            model="google_genai:gemini-3.5-flash-lite",
            tools=[get_weather, get_attractions],
            system_prompt="You are a helpful travel assistant",
        )
        
        # Invoke agent
        result = agent.invoke({
            "messages": [{
                "role": "user",
                "content": f"I'm visiting {city} from {start_date} to {end_date}. What should I do based on the weather?"
            }]
        })
        
        # Extract text and return as string
        response_text = result["messages"][-1].content
        
        # If it's a string, return it
        if isinstance(response_text, str):
            return response_text
        
        # If it's something else (list, dict, etc), convert to string
        return str(response_text)
    
    except Exception as e:
        return f"Error: {str(e)}"