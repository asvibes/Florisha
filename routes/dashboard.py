from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify
from extensions import db
from models.plant import Plant

dashboard_bp = Blueprint("dashboard", __name__)


def login_required(f):
    """Simple session-based login guard."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ──────────────────── DASHBOARD ───────────────
@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    
    user_id = session["user_id"]
    user_email = session["user_email"]

    # all plants belonging to this user, newest first
    plants = (Plant.query
              .filter_by(user_id=user_id)
              .order_by(Plant.id.desc())
              .all())

    # group by family for category tabs
    collection = {}
    for plant in plants:
        cat = plant.family or "Uncategorised"
        collection.setdefault(cat, []).append(plant)

    # stats
    total_identified = len(plants)
    total_categories = len(collection)
    latest_find      = plants[0] if plants else None

    # favourites
    favourites = [p for p in plants if p.is_favourite]

    return render_template(
        "dashboard.html",
        plants           = plants,
        collection       = collection,
        total_identified = total_identified,
        total_categories = total_categories,
        latest_find      = latest_find,
        favourites       = favourites,
        user_email       = user_email,
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