"""
models/journal_entry.py
-----------------------
Journal entry model. One row per user-created journal entry.
Linked to a Plant record but intentionally kept separate —
not every identification becomes a journal entry.
"""

from datetime import datetime
from extensions import db


class JournalEntry(db.Model):
    __tablename__ = "journal_entries"

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    plant_id        = db.Column(db.Integer, db.ForeignKey("plants.id"), nullable=True)

    # Plant snapshot — stored directly so entry survives plant deletion
    scientific_name = db.Column(db.String(200), nullable=True)
    common_name     = db.Column(db.String(200), nullable=True)
    image_url       = db.Column(db.String(300), nullable=True)

    # User content
    title           = db.Column(db.String(200), nullable=True)   # optional
    note            = db.Column(db.Text, nullable=True)           # optional

    created_at      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow,
                                onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user            = db.relationship("User",  backref=db.backref("journal_entries", lazy=True))
    plant           = db.relationship("Plant", backref=db.backref("journal_entries", lazy=True))