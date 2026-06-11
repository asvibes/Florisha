"""
routes/journal_routes.py
------------------------
Handles all journal entry CRUD.

Routes
------
POST /journal/save              — create a new entry from result page
GET  /journal/<id>              — fetch single entry as JSON (for right panel)
POST /journal/<id>/edit         — update title + note
POST /journal/<id>/delete       — delete entry
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from extensions import db
from models.journal_entry import JournalEntry
from models.plant import Plant

journal_bp = Blueprint("journal", __name__)


def _login_required():
    return "user_id" not in session


# ─────────────────────────────────────────────
# Save (create)
# ─────────────────────────────────────────────

@journal_bp.route("/journal/save", methods=["POST"])
def save():
    if _login_required():
        return jsonify({"success": False, "error": "Not logged in"}), 401

    data        = request.get_json(silent=True) or {}
    plant_id    = data.get("plant_id")
    title       = (data.get("title") or "").strip() or None
    note        = (data.get("note")  or "").strip() or None

    # Pull plant snapshot
    plant = Plant.query.get(plant_id) if plant_id else None

    entry = JournalEntry(
        user_id         = session["user_id"],
        plant_id        = plant.id            if plant else None,
        scientific_name = plant.scientific_name if plant else data.get("scientific_name"),
        common_name     = plant.name           if plant else data.get("common_name"),
        image_url       = plant.image_url      if plant else data.get("image_url"),
        title           = title,
        note            = note,
    )
    db.session.add(entry)
    db.session.commit()

    return jsonify({"success": True, "entry_id": entry.id})


# ─────────────────────────────────────────────
# Fetch single entry (JSON)
# ─────────────────────────────────────────────

@journal_bp.route("/journal/<int:entry_id>", methods=["GET"])
def get_entry(entry_id):
    if _login_required():
        return jsonify({"error": "Not logged in"}), 401

    entry = JournalEntry.query.get_or_404(entry_id)

    if entry.user_id != session["user_id"]:
        return jsonify({"error": "Forbidden"}), 403

    return jsonify({
        "id"             : entry.id,
        "title"          : entry.title or "",
        "note"           : entry.note  or "",
        "common_name"    : entry.common_name    or "",
        "scientific_name": entry.scientific_name or "",
        "image_url"      : entry.image_url       or "",
        "created_at"     : entry.created_at.strftime("%d %B %Y"),
    })


# ─────────────────────────────────────────────
# Edit
# ─────────────────────────────────────────────

@journal_bp.route("/journal/<int:entry_id>/edit", methods=["POST"])
def edit_entry(entry_id):
    if _login_required():
        return jsonify({"success": False}), 401

    entry = JournalEntry.query.get_or_404(entry_id)

    if entry.user_id != session["user_id"]:
        return jsonify({"success": False}), 403

    data        = request.get_json(silent=True) or {}
    entry.title = (data.get("title") or "").strip() or None
    entry.note  = (data.get("note")  or "").strip() or None
    db.session.commit()

    return jsonify({"success": True})


# ─────────────────────────────────────────────
# Delete
# ─────────────────────────────────────────────

@journal_bp.route("/journal/<int:entry_id>/delete", methods=["POST"])
def delete_entry(entry_id):
    if _login_required():
        return jsonify({"success": False}), 401

    entry = JournalEntry.query.get_or_404(entry_id)

    if entry.user_id != session["user_id"]:
        return jsonify({"success": False}), 403

    db.session.delete(entry)
    db.session.commit()

    return jsonify({"success": True})