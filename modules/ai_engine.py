import requests
from flask import current_app


def identify_plant(image_path):
    """
    Send an image to Pl@ntNet and return a clean result dict.

    Returns:
        {
            "success": True,
            "top": { scientific_name, common_name, family, genus, confidence },
            "alternatives": [ ...up to 4 results... ]
        }
        or
        {
            "success": False,
            "error": "reason"
        }
    """
    api_key = current_app.config["PLANTNET_API_KEY"]
    api_url = current_app.config["PLANTNET_API_URL"]

    # ── Send image to Pl@ntNet ──────────────────
    try:
        with open(image_path, "rb") as image_file:
            response = requests.post(
                api_url,
                params  = {"api-key": api_key, "lang": "en"},
                files   = {"images": image_file},
                timeout = 15
            )
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Pl@ntNet request timed out. Please try again."}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Could not reach Pl@ntNet: {str(e)}"}

    # ── Handle bad responses ────────────────────
    if response.status_code == 404:
        return {"success": False, "error": "No plant could be identified from this image."}

    if response.status_code != 200:
        return {"success": False, "error": f"Pl@ntNet returned an error (status {response.status_code})."}

    data = response.json()
    results = data.get("results", [])

    if not results:
        return {"success": False, "error": "No results returned. Try a clearer photo."}

    # ── Parse a single result ───────────────────
    def parse_result(r):
        species = r.get("species", {})
        common_names = species.get("commonNames", [])
        return {
            "scientific_name": species.get("scientificNameWithoutAuthor", "Unknown"),
            "common_name":     common_names[0] if common_names else None,
            "family":          species.get("family",  {}).get("scientificNameWithoutAuthor"),
            "genus":           species.get("genus",   {}).get("scientificNameWithoutAuthor"),
            "confidence":      round(r.get("score", 0), 4),
        }

    # ── Top result ──────────────────────────────
    top = parse_result(results[0])

    # ── Low confidence warning ──────────────────
    if top["confidence"] < 0.15:
        return {
            "success": False,
            "error": "Confidence too low to make a reliable identification. Try a clearer, closer photo."
        }

    # ── Alternatives (next 4) ───────────────────
    alternatives = [parse_result(r) for r in results[1:5]]

    return {
        "success":      True,
        "top":          top,
        "alternatives": alternatives,
    }