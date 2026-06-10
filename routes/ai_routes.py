import os
import uuid
import json
from datetime import datetime, timedelta
from flask import (Blueprint, request, redirect, url_for,
                   session, render_template, current_app, flash)
from extensions import db
from models.plant import Plant
from services.plant_processor import process_identification
from plantnet_service import identify_plant

ai_bp = Blueprint("ai", __name__)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def allowed_file(filename):
    allowed = current_app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def _redirect_on_failure():
    """Guests → identify page. Logged-in → dashboard identify section."""
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard") + "?section=identify")
    return redirect(url_for("ai.identify_page"))


def _clean_old_guest_uploads():
    """
    Delete guest upload files older than 30 minutes from the uploads folder.
    Called at the start of every new identify POST so no scheduler is needed.
    """
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    cutoff = datetime.utcnow() - timedelta(minutes=30)

    try:
        for fname in os.listdir(upload_folder):
            fpath = os.path.join(upload_folder, fname)
            if not os.path.isfile(fpath):
                continue
            modified = datetime.utcfromtimestamp(os.path.getmtime(fpath))
            if modified < cutoff:
                os.remove(fpath)
    except Exception:
        pass  # never crash the request over cleanup


def _build_plant_dict(source, image_url=None):
    """
    Build a normalized plant dict for the template from either:
    - a Plant ORM object  (logged-in path)
    - a PlantResult dataclass (guest path, top match)

    The template always uses the same keys regardless of source.
    """
    # Plant ORM object
    if isinstance(source, Plant):
        alternatives_raw = source.alternatives
        if isinstance(alternatives_raw, str):
            try:
                alternatives = json.loads(alternatives_raw)
            except (json.JSONDecodeError, TypeError):
                alternatives = []
        else:
            alternatives = alternatives_raw or []

        return {
            "common_name"    : source.name,
            "scientific_name": source.scientific_name,
            "family"         : source.family,
            "genus"          : source.genus,
            "confidence"     : source.confidence,
            "image_url"      : source.image_url,
            "alternatives"   : alternatives,
        }

    # PlantResult dataclass (guest)
    return {
        "common_name"    : source.common_name,
        "scientific_name": source.scientific_name,
        "family"         : source.family,
        "genus"          : source.genus,
        "confidence"     : source.confidence,
        "image_url"      : image_url or "",
        "alternatives"   : [
            {
                "common_name"    : alt.common_name,
                "scientific_name": alt.scientific_name,
                "family"         : alt.family,
                "genus"          : alt.genus,
                "confidence"     : alt.confidence,
            }
            for alt in (source.alternatives or [])
        ],
    }


# ─────────────────────────────────────────────
# Identify page (GET)
# ─────────────────────────────────────────────

@ai_bp.route("/identify", methods=["GET"])
def identify_page():
    """Standalone identify page for guests. Logged-in users go to dashboard."""
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard") + "?section=identify")
    return render_template("identify.html")


# ─────────────────────────────────────────────
# Identify (POST)
# ─────────────────────────────────────────────

@ai_bp.route("/identify", methods=["POST"])
def identify():
    # ── 1. Validate file ───────────────────────
    file = request.files.get("image")
    if not file or file.filename == "":
        flash("Please select an image to upload.", "error")
        return _redirect_on_failure()

    if not allowed_file(file.filename):
        flash("Unsupported file type. Please upload a JPG, PNG, or WebP image.", "error")
        return _redirect_on_failure()

    # ── 2. Clean up old guest uploads ─────────
    _clean_old_guest_uploads()

    # ── 3. Save image with a unique filename ───
    ext           = file.filename.rsplit(".", 1)[1].lower()
    filename      = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    image_path    = os.path.join(upload_folder, filename)
    file.save(image_path)

    # ── 4. Call PlantNet ───────────────────────
    plantnet_response = identify_plant(image_path)

    if not plantnet_response["success"]:
        if os.path.exists(image_path):
            os.remove(image_path)
        flash(plantnet_response["error"], "error")
        return _redirect_on_failure()

    plantnet_data = plantnet_response["data"]

    # ── 5. Process through enrichment pipeline ─
    result = process_identification(plantnet_data)

    if not result:
        if os.path.exists(image_path):
            os.remove(image_path)
        flash("Could not process the identification. Please try a clearer photo.", "error")
        return _redirect_on_failure()

    # ── 6. Logged-in user → save to DB ─────────
    if "user_id" in session:
        plant = Plant(
            user_id         = session["user_id"],
            name            = result.common_name or result.scientific_name,
            scientific_name = result.scientific_name,
            family          = result.family,
            genus           = result.genus,
            confidence      = result.confidence,
            image_url       = filename,
            alternatives    = json.dumps([
                {
                    "common_name"    : alt.common_name,
                    "scientific_name": alt.scientific_name,
                    "family"         : alt.family,
                    "genus"          : alt.genus,
                    "confidence"     : alt.confidence,
                }
                for alt in (result.alternatives or [])
            ]),
        )
        db.session.add(plant)
        db.session.commit()
        return redirect(url_for("ai.result", plant_id=plant.id))

    # ── 7. Guest → store result + filename in session ──
    else:
        session["guest_result"] = {
            "top": {
                "common_name"    : result.common_name,
                "scientific_name": result.scientific_name,
                "family"         : result.family,
                "genus"          : result.genus,
                "confidence"     : result.confidence,
            },
            "alternatives": [
                {
                    "common_name"    : alt.common_name,
                    "scientific_name": alt.scientific_name,
                    "family"         : alt.family,
                    "genus"          : alt.genus,
                    "confidence"     : alt.confidence,
                }
                for alt in (result.alternatives or [])
            ],
            "image_filename" : filename,
            "result_profile" : {
                "description"   : result.description,
                "origin_story"  : result.origin_story,
                "fun_fact"      : result.fun_fact,
                "emotional_note": result.emotional_note,
                "regional_notes": result.regional_notes,
                "care"          : result.care,
                "botanical"     : result.botanical,
                "safety"        : result.safety,
                "uses"          : result.uses,
                "seasons"       : result.seasons,
                "from_cache"    : result.from_cache,
            },
        }
        return redirect(url_for("ai.result_guest"))


# ─────────────────────────────────────────────
# Result — logged-in user
# ─────────────────────────────────────────────

@ai_bp.route("/result/<int:plant_id>")
def result(plant_id):
    plant_obj = Plant.query.get_or_404(plant_id)

    if "user_id" in session and plant_obj.user_id != session["user_id"]:
        return redirect(url_for("dashboard.dashboard"))

    # Re-fetch rich profile from cache for the result page
    from plant_knowledge import PlantKnowledge
    knowledge = PlantKnowledge.get_by_scientific_name(plant_obj.scientific_name)
    rich_profile = knowledge.profile if knowledge else {}

    plant_dict = _build_plant_dict(plant_obj)

    return render_template(
        "result.html",
        plant        = plant_dict,
        result_data  = rich_profile,
        is_guest     = False,
    )


# ─────────────────────────────────────────────
# Result — guest
# ─────────────────────────────────────────────

@ai_bp.route("/result/guest")
def result_guest():
    guest_result = session.pop("guest_result", None)

    if not guest_result:
        return redirect(url_for("home"))

    top           = guest_result["top"]
    alternatives  = guest_result.get("alternatives", [])
    image_filename = guest_result.get("image_filename", "")
    result_profile = guest_result.get("result_profile", {})

    plant_dict = {
        "common_name"    : top.get("common_name", ""),
        "scientific_name": top.get("scientific_name", ""),
        "family"         : top.get("family", ""),
        "genus"          : top.get("genus", ""),
        "confidence"     : top.get("confidence", 0),
        "image_url"      : image_filename,
        "alternatives"   : alternatives,
    }

    return render_template(
        "result.html",
        plant        = plant_dict,
        result_data  = result_profile,
        is_guest     = True,
    )


# ─────────────────────────────────────────────
# Guest image cleanup endpoint
# ─────────────────────────────────────────────

@ai_bp.route("/cleanup/<filename>", methods=["POST"])
def cleanup_guest_image(filename):
    """
    Called by JS on the guest result page after the image has loaded.
    Deletes the temporary guest upload from disk.
    Only allows deletion of files in the configured upload folder.
    """
    # Basic safety: strip any path traversal attempts
    safe_filename = os.path.basename(filename)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    file_path     = os.path.join(upload_folder, safe_filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass

    return {"status": "ok"}, 200