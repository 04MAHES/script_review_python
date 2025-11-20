import os 
import json
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_MODEL = os.getenv("GEMINI_API_MODEL")
GEMINI_API_URL = os.getenv("GEMINI_API_URL")

PROMPT_TEMPLATE = """
You are an expert RPA code reviewer specializing in %s development.
Analyze the following workflow file.

Respond ONLY with valid JSON in this exact schema:
{
  "tool": "<UiPath or Blue Prism>",
  "compliance_score": 0,
  "issues": ["issue1", "issue2"],
  "recommendations": ["rec1", "rec2"]
}

Workflow content:
%s
"""

def call_gemini_api(prompt: str) -> str:
    print('Inside Gemini client')
    if not GEMINI_API_KEY or not GEMINI_API_URL:
        raise ValueError("Gemini API configuration missing")

    # Google Gemini API requires key in URL
    url = f"{GEMINI_API_URL}?key={GEMINI_API_KEY}"

    headers = {
        "Content-Type": "application/json"
    }

    # Correct request body structure
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    logger.info("Calling Gemini API -> %s", url)
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()

    data = resp.json()

    # Correct response extraction
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return str(data)
