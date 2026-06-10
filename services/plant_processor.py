"""
plant_processor.py
------------------
The main orchestration layer for Flourisha's smart plant memory system.

Flow
────
1.  PlantNet identifies the uploaded image  →  returns raw result dict
2.  We extract the best match + alternatives
3.  We check PlantKnowledge cache for the species
4.  Cache hit  → return stored profile immediately (fast path)
    Cache miss → call Gemini, store result, return profile
5.  We merge everything into a single PlantResult object
    ready for the Jinja template.

Usage (inside a Flask route)
─────────────────────────────
from plant_processor import process_identification

result = process_identification(plantnet_data, user_id=current_user.id)
# result is a PlantResult (dataclass)
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from gemini_service import generate_plant_profile
from plant_knowledge import PlantKnowledge

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class AlternativeMatch:
    scientific_name: str
    common_name: str
    family: str
    genus: str
    confidence: float


@dataclass
class PlantResult:
    # Core identity (from PlantNet)
    scientific_name : str
    common_name     : str
    family          : str
    genus           : str
    confidence      : float

    # Rich profile (from Gemini / cache)
    description     : str = ""
    origin_story    : str = ""
    fun_fact        : str = ""
    emotional_note  : str = ""
    regional_notes  : str = ""

    care            : dict = field(default_factory=dict)
    botanical       : dict = field(default_factory=dict)
    safety          : dict = field(default_factory=dict)
    uses            : dict = field(default_factory=dict)
    seasons         : dict = field(default_factory=dict)

    alternatives    : list[AlternativeMatch] = field(default_factory=list)

    # Metadata
    from_cache      : bool = False   # True if knowledge was already stored
    knowledge_id    : Optional[int] = None


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_best_match(plantnet_data: dict) -> dict:
    """
    Pull the top result from a PlantNet API response dict.
    PlantNet shape:
      { "results": [ { "score": float, "species": { ... }, "gbif": { ... } }, ... ] }
    """
    results = plantnet_data.get("results", [])
    if not results:
        return {}

    best = results[0]
    species = best.get("species", {})

    scientific_name = species.get("scientificNameWithoutAuthor", "")
    family          = species.get("family", {}).get("scientificNameWithoutAuthor", "")
    genus           = species.get("genus", {}).get("scientificNameWithoutAuthor", "")
    common_names    = species.get("commonNames", [])
    common_name     = common_names[0] if common_names else ""
    confidence      = round(float(best.get("score", 0)), 4)

    return {
        "scientific_name": scientific_name,
        "common_name"    : common_name,
        "family"         : family,
        "genus"          : genus,
        "confidence"     : confidence,
    }


def _extract_alternatives(plantnet_data: dict, skip_first: bool = True) -> list[AlternativeMatch]:
    """Return up to 4 alternative matches (everything after the top result)."""
    results = plantnet_data.get("results", [])
    start   = 1 if skip_first else 0
    alts    = []

    for item in results[start:start + 4]:
        species = item.get("species", {})
        common_names = species.get("commonNames", [])
        alts.append(AlternativeMatch(
            scientific_name = species.get("scientificNameWithoutAuthor", ""),
            common_name     = common_names[0] if common_names else "",
            family          = species.get("family", {}).get("scientificNameWithoutAuthor", ""),
            genus           = species.get("genus", {}).get("scientificNameWithoutAuthor", ""),
            confidence      = round(float(item.get("score", 0)), 4),
        ))

    return alts


def _profile_to_result_fields(profile: dict) -> dict:
    """Map a Gemini profile dict onto PlantResult keyword args."""
    return {
        "description"    : profile.get("description", ""),
        "origin_story"   : profile.get("origin_story", ""),
        "fun_fact"       : profile.get("fun_fact", ""),
        "emotional_note" : profile.get("emotional_note", ""),
        "regional_notes" : profile.get("regional_notes", ""),
        "care"           : profile.get("care", {}),
        "botanical"      : profile.get("botanical", {}),
        "safety"         : profile.get("safety", {}),
        "uses"           : profile.get("uses", {}),
        "seasons"        : profile.get("seasons", {}),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def process_identification(plantnet_data: dict) -> Optional[PlantResult]:
    """
    Main entry point.

    Args:
        plantnet_data: Raw dict returned by the PlantNet API.

    Returns:
        PlantResult with full profile, or None if identification failed.
    """
    best = _extract_best_match(plantnet_data)
    if not best or not best.get("scientific_name"):
        logger.warning("process_identification: no valid best match found.")
        return None

    scientific_name = best["scientific_name"]
    common_name     = best["common_name"]
    family          = best["family"]
    genus           = best["genus"]
    confidence      = best["confidence"]
    alternatives    = _extract_alternatives(plantnet_data)

    # ── 1. Check memory cache ──────────────────────────────────────────────
    knowledge   = PlantKnowledge.get_by_scientific_name(scientific_name)
    from_cache  = False

    if knowledge and knowledge.profile:
        logger.info("Cache HIT for '%s' (id=%s).", scientific_name, knowledge.id)
        profile    = knowledge.profile
        from_cache = True
        PlantKnowledge.increment_lookup(scientific_name)
    else:
        # ── 2. Cache miss → call Gemini ────────────────────────────────────
        logger.info("Cache MISS for '%s'. Calling Gemini…", scientific_name)
        profile = generate_plant_profile(
            scientific_name = scientific_name,
            common_name     = common_name,
            family          = family,
            genus           = genus,
        ) or {}

        # ── 3. Persist to memory ───────────────────────────────────────────
        if profile:
            knowledge = PlantKnowledge.save_profile(
                scientific_name = scientific_name,
                profile_data    = profile,
                common_name     = common_name,
                family          = family,
                genus           = genus,
            )

    # ── 4. Assemble PlantResult ────────────────────────────────────────────
    result = PlantResult(
        scientific_name = scientific_name,
        common_name     = common_name,
        family          = family,
        genus           = genus,
        confidence      = confidence,
        alternatives    = alternatives,
        from_cache      = from_cache,
        knowledge_id    = knowledge.id if knowledge else None,
        **_profile_to_result_fields(profile),
    )

    return result