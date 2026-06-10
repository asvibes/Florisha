"""
plantnet_service.py
-------------------
Handles all PlantNet API interactions for Flourisha.

Install:  pip install requests
Env/Config: PLANTNET_API_KEY, PLANTNET_API_URL

Usage:
    from plantnet_service import identify_plant
    result = identify_plant(image_path)
    # result is a dict: { "success": bool, "data": dict | None, "error": str | None }
"""

import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)


def identify_plant(image_path: str) -> dict:
    """
    Send an image to the PlantNet API and return the raw response dict.

    Args:
        image_path: Absolute or relative path to the image file on disk.

    Returns:
        {
            "success": True,
            "data": { ...raw PlantNet response... }
        }
        or
        {
            "success": False,
            "data": None,
            "error": "Human-readable error message"
        }
    """
    api_key = current_app.config.get("PLANTNET_API_KEY")
    api_url = current_app.config.get("PLANTNET_API_URL")

    if not api_key:
        logger.error("PLANTNET_API_KEY is not configured.")
        return {"success": False, "data": None, "error": "Plant identification service is not configured."}

    if not api_url:
        logger.error("PLANTNET_API_URL is not configured.")
        return {"success": False, "data": None, "error": "Plant identification service URL is not configured."}

    try:
        with open(image_path, "rb") as image_file:
            files = [("images", (image_path, image_file, "image/jpeg"))]
            params = {"api-key": api_key}

            response = requests.post(
                api_url,
                files=files,
                params=params,
                timeout=30,
            )

        if response.status_code == 404:
            logger.warning("PlantNet returned 404 — no species matched.")
            return {"success": False, "data": None, "error": "No plant species could be matched. Try a clearer photo."}

        if response.status_code != 200:
            logger.error("PlantNet API error: %s %s", response.status_code, response.text)
            return {"success": False, "data": None, "error": f"Identification service returned an error ({response.status_code})."}

        data = response.json()

        if not data.get("results"):
            logger.warning("PlantNet returned empty results for image: %s", image_path)
            return {"success": False, "data": None, "error": "No results returned. Try a closer or clearer photo."}

        logger.info("PlantNet identified plant from: %s", image_path)
        return {"success": True, "data": data, "error": None}

    except FileNotFoundError:
        logger.error("Image file not found: %s", image_path)
        return {"success": False, "data": None, "error": "Uploaded image could not be found."}

    except requests.exceptions.Timeout:
        logger.error("PlantNet request timed out for: %s", image_path)
        return {"success": False, "data": None, "error": "Identification timed out. Please try again."}

    except requests.exceptions.RequestException as exc:
        logger.error("PlantNet request failed: %s", exc)
        return {"success": False, "data": None, "error": "Could not reach the identification service. Please try again."}

    except Exception as exc:
        logger.error("Unexpected error in identify_plant: %s", exc)
        return {"success": False, "data": None, "error": "An unexpected error occurred during identification."}