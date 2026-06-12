from flask import Blueprint, render_template, redirect, url_for, session, jsonify, current_app
from extensions import db
from models.plant import Plant
from models.journal_entry import JournalEntry
from models.calendar_preference import CalendarPreference
from utils.cloudinary_helper import delete_image

dashboard_bp = Blueprint("dashboard", __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ──────────────────── DASHBOARD ───────────────
@dashboard_bp.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    user_id    = session["user_id"]
    user_email = session.get("user_email", "")

    plants     = Plant.query.filter_by(user_id=user_id).order_by(Plant.created_at.desc()).all()
    favourites = [p for p in plants if p.is_favourite]

    collection = {}
    for plant in plants:
        cat = plant.family or "Uncategorised"
        collection.setdefault(cat, []).append(plant)

    total_identified = len(plants)
    total_categories = len(collection)
    latest_find      = plants[0] if plants else None

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
        journal_entries  = journal_entries,
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

    # Delete Cloudinary image only if no journal entry still references it
    if plant.image_url:
        still_referenced = JournalEntry.query.filter_by(
            image_url=plant.image_url
        ).first()

        if not still_referenced:
            delete_image(plant.image_url)

    # Remove calendar preferences referencing this plant first,
    # otherwise the foreign key constraint blocks the delete
    CalendarPreference.query.filter_by(plant_id=plant_id).delete()

    db.session.delete(plant)
    db.session.commit()

    return jsonify({"success": True})