"""
gemini_service.py
-----------------
Handles all Gemini AI interactions for Flourisha.
Uses google-generativeai SDK.

Install:  pip install google-generativeai
Env var:  GEMINI_API_KEY
"""

import os
import json
import logging
import re
import google.generativeai as genai
from typing import Optional
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

_GEMINI_MODEL = "models/gemini-1.5-pro"   # fast + cheap; swap to gemini-1.5-pro for depth

def _get_client() -> genai.GenerativeModel:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("GEMINI_API_KEY is not set in environment variables.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(_GEMINI_MODEL)


# ---------------------------------------------------------------------------
# Core prompt
# ---------------------------------------------------------------------------

_PLANT_PROMPT = """
You are a knowledgeable botanist with a warm, storytelling voice.
Given the plant details below, produce a rich but human JSON profile.

Plant details:
  Scientific name : {scientific_name}
  Common name     : {common_name}
  Family          : {family}
  Genus           : {genus}

Return ONLY valid JSON — no markdown fences, no extra text.

Schema (use exactly these keys):

{{
  "description": "2-3 sentences. Feel like a nature guide discovering this plant for the first time.",

  "origin_story": "1-2 sentences on where this plant originates / its natural habitat.",

  "fun_fact": "One surprising or delightful fact most people don't know.",

  "care": {{
    "sunlight": "e.g. Full sun / partial shade — add a one-line tip",
    "water": "Frequency & technique",
    "soil": "Preferred soil type",
    "humidity": "Ideal humidity range or note",
    "temperature": "Preferred temperature range",
    "fertiliser": "How and when to feed",
    "pruning": "When and how to prune, or 'Not needed'",
    "difficulty": "Beginner / Intermediate / Expert"
  }},

  "botanical": {{
    "leaf_type": "e.g. Simple, ovate, dark green",
    "flower": "Colour, season, or 'Does not flower commonly'",
    "fruit_seed": "Description or 'None'",
    "growth_rate": "Slow / Medium / Fast",
    "mature_size": "Height × spread in cm"
  }},

  "safety": {{
    "toxic_to_humans": true or false,
    "toxic_to_pets": true or false,
    "notes": "Detail on toxicity or 'Safe for most people and pets.'"
  }},

  "uses": {{
    "medicinal": "Traditional or modern medicinal uses, or 'None documented'",
    "culinary": "Edible parts and uses, or 'Not edible'",
    "ayurvedic": "Ayurvedic relevance if any, else omit this key entirely",
    "ornamental": "How it is used decoratively"
  }},

  "seasons": {{
    "best_growing": "Season(s) when it thrives",
    "bloom_time": "If it flowers — season, else 'N/A'",
    "dormancy": "Does it go dormant? When?"
  }},

  "regional_notes": "1-2 sentences on how it fares in India (especially north India / UP) if relevant, else a general climate note.",

  "emotional_note": "A single warm sentence — what feeling or memory this plant tends to evoke in people."
}}
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_plant_profile(
    scientific_name: str,
    common_name: str = "",
    family: str = "",
    genus: str = "",
) -> Optional[dict]:
    """
    Call Gemini to produce a structured plant profile.
    Returns a parsed dict on success, None on failure.
    """
    prompt = _PLANT_PROMPT.format(
        scientific_name=scientific_name or "Unknown",
        common_name=common_name or "Unknown",
        family=family or "Unknown",
        genus=genus or "Unknown",
    )

    try:
        model = _get_client()
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # strip any accidental ```json ... ``` wrapping
        raw = re.sub(r"^```(?:json)?", "", raw).rstrip("`").strip()

        data = json.loads(raw)
        logger.info("Gemini profile generated for '%s'.", scientific_name)
        return data

    except json.JSONDecodeError as exc:
        logger.error("Gemini returned non-JSON for '%s': %s", scientific_name, exc)
        return None
    except Exception as exc:
        logger.error("Gemini API error for '%s': %s", scientific_name, exc)
        return None