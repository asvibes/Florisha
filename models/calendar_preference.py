# models/calendar_preference.py
# ─────────────────────────────────────────────
# Stores the user's chosen "cover" plant for a
# specific calendar date.
# ─────────────────────────────────────────────

from extensions import db
from datetime import datetime


class CalendarPreference(db.Model):
    __tablename__ = "calendar_preferences"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date       = db.Column(db.Date,    nullable=False)          # e.g. 2026-06-11
    plant_id   = db.Column(db.Integer, db.ForeignKey("plants.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "date", name="uq_user_date"),
    )

    def __repr__(self):
        return f"<CalendarPreference user={self.user_id} date={self.date} plant={self.plant_id}>"