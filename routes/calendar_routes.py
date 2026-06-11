# routes/calendar_routes.py
# ─────────────────────────────────────────────
# Two endpoints:
#   GET  /calendar/data          — month JSON for the JS grid
#   POST /calendar/preference    — save chosen cover plant for a date
# ─────────────────────────────────────────────

from flask import Blueprint, request, jsonify, session
from extensions import db
from models.plant import Plant
from models.journal_entry import JournalEntry
from models.calendar_preference import CalendarPreference

from datetime import date, timedelta
import calendar

calendar_bp = Blueprint("calendar", __name__)


def _login_required():
    return "user_id" not in session


# ─────────────────────────────────────────────
# Helper: first & last day of a month
# ─────────────────────────────────────────────

def _month_bounds(year: int, month: int):
    first = date(year, month, 1)
    last_day = calendar.monthrange(year, month)[1]
    last = date(year, month, last_day)
    return first, last


# ─────────────────────────────────────────────
# GET /calendar/data?year=2026&month=6
# ─────────────────────────────────────────────

@calendar_bp.route("/calendar/data", methods=["GET"])
def calendar_data():
    if _login_required():
        return jsonify({"error": "Not logged in"}), 401

    user_id = session["user_id"]

    # Parse year/month — default to today
    today = date.today()
    try:
        year  = int(request.args.get("year",  today.year))
        month = int(request.args.get("month", today.month))
        # clamp month
        month = max(1, min(12, month))
    except (ValueError, TypeError):
        year, month = today.year, today.month

    first_day, last_day = _month_bounds(year, month)

    # ── Fetch all plants in this month ──────────────────────────────────
    plants = (
        Plant.query
        .filter(
            Plant.user_id   == user_id,
            Plant.created_at >= first_day,
            Plant.created_at <= last_day + timedelta(days=1),
        )
        .order_by(Plant.created_at.asc())
        .all()
    )

    # ── Fetch journal entries (to flag which plants have one) ───────────
    # We key on plant_id for fast lookup
    journal_plant_ids = set(
        row.plant_id
        for row in JournalEntry.query
        .filter_by(user_id=user_id)
        .with_entities(JournalEntry.plant_id)
        .all()
        if row.plant_id is not None
    )

    # Also fetch journal entries that have a date in this month
    # (some entries may not be linked to a plant)
    journal_entries = (
        JournalEntry.query
        .filter(
            JournalEntry.user_id   == user_id,
            JournalEntry.created_at >= first_day,
            JournalEntry.created_at <= last_day + timedelta(days=1),
        )
        .order_by(JournalEntry.created_at.asc())
        .all()
    )

    # ── Fetch user's thumbnail preferences for this month ───────────────
    prefs = (
        CalendarPreference.query
        .filter(
            CalendarPreference.user_id == user_id,
            CalendarPreference.date   >= first_day,
            CalendarPreference.date   <= last_day,
        )
        .all()
    )
    pref_map = { str(p.date): p.plant_id for p in prefs }

    # ── Group plants by date ─────────────────────────────────────────────
    days_data = {}  # "YYYY-MM-DD" → { plants: [...], journal_entries: [...] }

    for plant in plants:
        d = str(plant.created_at.date())
        days_data.setdefault(d, {"plants": [], "journal_entries": []})
        days_data[d]["plants"].append({
            "id"        : plant.id,
            "name"      : plant.name or plant.scientific_name or "Unknown",
            "image_url" : plant.image_url or "",
            "has_journal": plant.id in journal_plant_ids,
        })

    for entry in journal_entries:
        d = str(entry.created_at.date())
        days_data.setdefault(d, {"plants": [], "journal_entries": []})
        days_data[d]["journal_entries"].append({
            "id"          : entry.id,
            "title"       : entry.title or entry.common_name or "Untitled",
            "common_name" : entry.common_name or "",
            "image_url"   : entry.image_url or "",
        })

    # ── Attach chosen cover thumbnail ────────────────────────────────────
    for d, data in days_data.items():
        chosen_plant_id = pref_map.get(d)
        if chosen_plant_id:
            # find the plant in today's list
            match = next((p for p in data["plants"] if p["id"] == chosen_plant_id), None)
            data["cover"] = match or (data["plants"][0] if data["plants"] else None)
        else:
            data["cover"] = data["plants"][0] if data["plants"] else None

    return jsonify({
        "year"     : year,
        "month"    : month,
        "days"     : days_data,
        "today"    : str(today),
        "pref_map" : pref_map,
    })


# ─────────────────────────────────────────────
# POST /calendar/preference
# body: { "date": "2026-06-11", "plant_id": 42 }
# ─────────────────────────────────────────────

@calendar_bp.route("/calendar/preference", methods=["POST"])
def set_preference():
    if _login_required():
        return jsonify({"success": False, "error": "Not logged in"}), 401

    user_id = session["user_id"]
    data    = request.get_json(silent=True) or {}

    date_str = data.get("date")
    plant_id = data.get("plant_id")

    if not date_str or not plant_id:
        return jsonify({"success": False, "error": "Missing date or plant_id"}), 400

    try:
        chosen_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date"}), 400

    # Verify the plant belongs to this user
    plant = Plant.query.filter_by(id=plant_id, user_id=user_id).first()
    if not plant:
        return jsonify({"success": False, "error": "Plant not found"}), 404

    # Upsert
    pref = CalendarPreference.query.filter_by(
        user_id=user_id,
        date=chosen_date,
    ).first()

    if pref:
        pref.plant_id = plant_id
    else:
        pref = CalendarPreference(
            user_id  = user_id,
            date     = chosen_date,
            plant_id = plant_id,
        )
        db.session.add(pref)

    db.session.commit()
    return jsonify({"success": True})