import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("API_KEY")

client = genai.Client(api_key=api_key)

class ExtractedLocations(BaseModel):
    detected_locations: list[str] = Field(..., description="List of detected location names")

def extract_locations_with_llm(text: str) -> list[str]:
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=(
                    "You are a strict data-mining parser for an urban grid. "
                    "Your job is to analyze the user's text and extract ONLY explicit, micro-level geographic names "
                    "or neighborhoods inside Chennai (e.g., Perungalathur, Thoraipakkam, Egmore, Mylapore, Adyar) "
                    "mentioned as the source of the grievance. "
                    "CRITICAL: Completely ignore generic words like 'power', 'eb', 'office', 'help', 'line', 'look'. "
                    "Ignore city-level words like 'Chennai' unless it refers to a specific transport hub like 'Chennai Egmore'. "
                    "Extract only the raw base location name out of conversational text."
                ),
                response_mime_type="application/json",
                response_schema=ExtractedLocations,
            )
        )

        import json
        data = json.loads(response.text)
        return data.get("detected_locations", [])
    
    except Exception as e:
        print(f"LLM Extraction Error: {e}")
        return []