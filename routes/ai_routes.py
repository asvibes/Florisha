import os
import uuid
from flask import (Blueprint, request, redirect, url_for,
                   session, render_template, current_app, flash)
from extensions import db
from models.plant import Plant
from modules.ai_engine import identify_plant

ai_bp = Blueprint("ai", __name__)


def allowed_file(filename):
    """Check the file extension is in the allowed set."""
    allowed = current_app.config["ALLOWED_EXTENSIONS"]
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


# ──────────────────── IDENTIFY PAGE (GET) ─────
@ai_bp.route("/identify", methods=["GET"])
def identify_page():
    """
    Standalone identify page — guests only.
    Logged-in users are sent to their dashboard instead.
    """
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard") + "?section=identify")
    return render_template("identify.html")


# ──────────────────── IDENTIFY (POST) ─────────
@ai_bp.route("/identify", methods=["POST"])
def identify():

    # ── 1. Check a file was actually uploaded ──
    if "image" not in request.files:
        flash("No file received. Please try again.", "error")
        return _redirect_on_failure()

    file = request.files["image"]

    if file.filename == "":
        flash("No file selected.", "error")
        return _redirect_on_failure()

    if not allowed_file(file.filename):
        flash("Only JPG, PNG, and WEBP images are supported.", "error")
        return _redirect_on_failure()

    # ── 2. Save image with a unique filename ───
    ext           = file.filename.rsplit(".", 1)[1].lower()
    filename      = f"{uuid.uuid4().hex}.{ext}"
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    image_path    = os.path.join(upload_folder, filename)
    file.save(image_path)

    # ── 3. Call Pl@ntNet ───────────────────────
    result = identify_plant(image_path)

    if not result["success"]:
        if os.path.exists(image_path):
            os.remove(image_path)
        flash(result["error"], "error")
        return _redirect_on_failure()

    top          = result["top"]
    alternatives = result["alternatives"]

    # ── 4. Logged-in user → save to DB ─────────
    if "user_id" in session:
        plant = Plant(
            user_id         = session["user_id"],
            name            = top["common_name"] or top["scientific_name"],
            scientific_name = top["scientific_name"],
            family          = top["family"],
            genus           = top["genus"],
            confidence      = top["confidence"],
            image_url       = filename,          # store filename only, served via /uploads/
            alternatives    = alternatives,      # list of dicts saved as JSON
        )
        db.session.add(plant)
        db.session.commit()

        return redirect(url_for("ai.result", plant_id=plant.id))

    # ── 5. Guest → store result in session, delete image ──
    else:
        if os.path.exists(image_path):
            os.remove(image_path)

        session["guest_result"] = {
            "top":          top,
            "alternatives": alternatives,
        }
        return redirect(url_for("ai.result_guest"))


# ──────────────────── RESULT (logged-in) ──────
@ai_bp.route("/result/<int:plant_id>")
def result(plant_id):
    plant = Plant.query.get_or_404(plant_id)

    # make sure the plant belongs to the session user
    if "user_id" in session and plant.user_id != session["user_id"]:
        return redirect(url_for("dashboard.dashboard"))

    return render_template("result.html",
                           plant        = plant,
                           alternatives = plant.alternatives or [],
                           is_guest     = False)


# ──────────────────── RESULT (guest) ──────────
@ai_bp.route("/result/guest")
def result_guest():
    guest_result = session.pop("guest_result", None)

    if not guest_result:
        return redirect(url_for("home"))

    return render_template("result.html",
                           plant        = guest_result["top"],
                           alternatives = guest_result["alternatives"],
                           is_guest     = True)


# ──────────────────── HELPERS ─────────────────
def _redirect_on_failure():
    """
    Guests → back to standalone identify page.
    Logged-in users → back to dashboard identify section.
    Both carry the flash message set before calling this.
    """
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard") + "?section=identify")
    return redirect(url_for("ai.identify_page"))