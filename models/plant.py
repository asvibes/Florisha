from extensions import db
from sqlalchemy import JSON
from datetime import datetime


class Plant(db.Model):
    __tablename__ = "plants"

    id              = db.Column(db.Integer, primary_key=True)

    # core identity
    name            = db.Column(db.String(100),  nullable=True)   # common name — nullable, fallback to scientific_name
    scientific_name = db.Column(db.String(150))
    family          = db.Column(db.String(100))
    genus           = db.Column(db.String(100))                   # NEW — from Pl@ntNet genus field
    confidence      = db.Column(db.Float)
    image_url       = db.Column(db.String(300))

    # identification alternatives — stored as JSON list of dicts
    # each dict: { scientific_name, common_name, family, genus, confidence }
    alternatives    = db.Column(JSON, nullable=True)              # NEW

    # timestamps
    created_at      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # relations / flags
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    is_favourite    = db.Column(db.Boolean, default=False, nullable=False, server_default="0")