from flask import Blueprint, render_template, redirect, url_for, session, jsonify, current_app
from extensions import db
from models.plant import Plant
import os
from models.journal_entry import JournalEntry
from flask import Blueprint, render_template, session, redirect, url_for
from models.plant import Plant   # if you're using Plant model here
dashboard_bp = Blueprint("dashboard", __name__)


def login_required(f):
    """Simple session-based login guard."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))   # ← was url_for("login"), which doesn't exist
        return f(*args, **kwargs)
    return decorated


# ──────────────────── DASHBOARD ───────────────
@dashboard_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
 
    user_id = session["user_id"]
    user_email = session.get("user_email", "")
 
    # ── Plants ──────────────────────────────────────────────────────────
    plants     = Plant.query.filter_by(user_id=user_id).order_by(Plant.created_at.desc()).all()
    favourites = [p for p in plants if p.is_favourite]
 
    # Category grouping for tabs
    collection = {}
    for plant in plants:
        cat = plant.family or "Uncategorised"
        collection.setdefault(cat, []).append(plant)
 
    total_identified = len(plants)
    total_categories = len(collection)
    latest_find      = plants[0] if plants else None
 
    # ── Journal entries ─────────────────────────────────────────────────
    journal_entries = (
        JournalEntry.query
        .filter_by(user_id=user_id)
        .order_by(JournalEntry.created_at.desc())
        .all()
    )
 
    return render_template(
        "dashboard.html",
        user_email       = user_email,
        plants           = plants,
        favourites       = favourites,
        collection       = collection,
        total_identified = total_identified,
        total_categories = total_categories,
        latest_find      = latest_find,
        journal_entries  = journal_entries,        # ← new
    )

# ──────────────────── FAVOURITE TOGGLE ────────
@dashboard_bp.route("/favourite/<int:plant_id>", methods=["POST"])
@login_required
def toggle_favourite(plant_id):
    user_id = session["user_id"]

    plant = Plant.query.filter_by(id=plant_id, user_id=user_id).first()
    if not plant:
        return jsonify({"error": "Not found"}), 404

    plant.is_favourite = not plant.is_favourite
    db.session.commit()

    return jsonify({"is_favourite": plant.is_favourite})


# ──────────────────── DELETE PLANT ────────────
@dashboard_bp.route("/plant/<int:plant_id>/delete", methods=["POST"])
@login_required
def delete_plant(plant_id):
    user_id = session["user_id"]

    plant = Plant.query.filter_by(id=plant_id, user_id=user_id).first()
    if not plant:
        return jsonify({"error": "Not found"}), 404

    # delete image from disk if it exists
    if plant.image_url:
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        image_path    = os.path.join(upload_folder, os.path.basename(plant.image_url))
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception:
                pass  # don't block deletion if file removal fails

    db.session.delete(plant)
    db.session.commit()

    return jsonify({"success": True})

