from extensions import db
from datetime import datetime

class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)

    # email verification
    is_verified          = db.Column(db.Boolean, default=False, nullable=False)
    verification_token   = db.Column(db.String(100), unique=True, nullable=True)
    token_expiry         = db.Column(db.DateTime, nullable=True)
    
    # password reset
    reset_token        = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)