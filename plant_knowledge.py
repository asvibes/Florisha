"""
plant_knowledge.py
------------------
SQLAlchemy model that stores the rich AI-generated profile for each unique plant
(keyed by scientific_name).

This is the "memory" layer.  Once a profile exists, Gemini is never called again
for the same species.

Add to your create_all() call so the table is created automatically.
"""

import json
from datetime import datetime
from extensions import db
from sqlalchemy import Text


class PlantKnowledge(db.Model):
    """
    One row per unique plant species.
    Keyed on scientific_name (lowercased + stripped).
    """
    __tablename__ = "plant_knowledge"

    id              = db.Column(db.Integer, primary_key=True)
    scientific_name = db.Column(db.String(200), unique=True, nullable=False, index=True)
    common_name     = db.Column(db.String(200), nullable=True)
    family          = db.Column(db.String(100), nullable=True)
    genus           = db.Column(db.String(100), nullable=True)

    # Rich structured data — stored as JSON text
    profile_json    = db.Column(Text, nullable=True)

    # Metadata
    created_at      = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow,
                                onupdate=datetime.utcnow, nullable=False)
    times_looked_up = db.Column(db.Integer, default=0, nullable=False)

    # -----------------------------------------------------------------------
    # Convenience helpers
    # -----------------------------------------------------------------------

    @property
    def profile(self) -> dict:
        """Return the stored profile as a Python dict (empty dict if missing)."""
        if not self.profile_json:
            return {}
        try:
            return json.loads(self.profile_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    @profile.setter
    def profile(self, data: dict):
        """Serialise a dict into the profile_json column."""
        self.profile_json = json.dumps(data, ensure_ascii=False)

    @classmethod
    def _normalise_key(cls, scientific_name: str) -> str:
        return scientific_name.strip().lower()

    # -----------------------------------------------------------------------
    # Lookup / upsert
    # -----------------------------------------------------------------------

    @classmethod
    def get_by_scientific_name(cls, scientific_name: str) -> "PlantKnowledge | None":
        """Return the stored knowledge row, or None if not found."""
        key = cls._normalise_key(scientific_name)
        return cls.query.filter_by(scientific_name=key).first()

    @classmethod
    def save_profile(
        cls,
        scientific_name: str,
        profile_data: dict,
        common_name: str = "",
        family: str = "",
        genus: str = "",
    ) -> "PlantKnowledge":
        """
        Create or update the knowledge row for a species.
        Returns the saved instance.
        """
        key = cls._normalise_key(scientific_name)
        knowledge = cls.query.filter_by(scientific_name=key).first()

        if knowledge is None:
            knowledge = cls(scientific_name=key)
            db.session.add(knowledge)

        knowledge.common_name = common_name or knowledge.common_name
        knowledge.family      = family or knowledge.family
        knowledge.genus       = genus or knowledge.genus
        knowledge.profile     = profile_data
        knowledge.updated_at  = datetime.utcnow()

        db.session.commit()
        return knowledge

    @classmethod
    def increment_lookup(cls, scientific_name: str):
        """Bump the times_looked_up counter (call after each result view)."""
        key = cls._normalise_key(scientific_name)
        knowledge = cls.query.filter_by(scientific_name=key).first()
        if knowledge:
            knowledge.times_looked_up = (knowledge.times_looked_up or 0) + 1
            db.session.commit()