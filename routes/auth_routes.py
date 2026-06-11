import os
import secrets
from datetime import datetime, timedelta
import resend
from flask import (Blueprint, render_template, redirect,
                   url_for, session, request, flash)
from extensions import db, bcrypt
from models.user import User

auth_bp = Blueprint("auth", __name__)


# ── helpers ──────────────────────────────────────────────

def send_verification_email(user):
    token  = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=1)

    user.verification_token = token
    user.token_expiry       = expiry
    db.session.commit()

    link = url_for("auth.verify_email", token=token, _external=True)

    resend.api_key = os.getenv("RESEND_API_KEY")

    resend.Emails.send({
        "from": "Florisha <onboarding@resend.dev>",
        "to": user.email,
        "subject": "Verify your Florisha account",
        "text": (
            f"Hi,\n\n"
            f"Thanks for joining Florisha! Click the link below to verify "
            f"your email address. This link expires in 1 hour.\n\n"
            f"{link}\n\n"
            f"If you didn't create an account, you can ignore this email.\n\n"
            f"— The Florisha Team"
        )
    })


# ── REGISTER ─────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email            = request.form.get("email", "").strip().lower()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or not password or not confirm_password:
            return render_template("register.html", error="All fields are required.")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match.")

        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters.")

        if User.query.filter_by(email=email).first():
            return render_template("register.html", error="An account with that email already exists.")

        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
        new_user  = User(email=email, password=hashed_pw, is_verified=False)
        db.session.add(new_user)
        db.session.commit()

        send_verification_email(new_user)
        session["pending_email"] = email

        return redirect(url_for("auth.verify_pending"))

    return render_template("register.html")


# ── VERIFY PENDING ────────────────────────────────────────

@auth_bp.route("/verify-pending")
def verify_pending():
    email = session.get("pending_email", "")
    return render_template("verify_email.html", email=email)


# ── VERIFY LINK ───────────────────────────────────────────

@auth_bp.route("/verify/<token>")
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()

    if not user:
        return render_template("verify_email.html",
                               error="Invalid or already used verification link.",
                               email="")

    if datetime.utcnow() > user.token_expiry:
        session["pending_email"] = user.email
        return render_template("verify_email.html",
                               error="This link has expired. Request a new one below.",
                               email=user.email)

    user.is_verified          = True
    user.verification_token   = None
    user.token_expiry         = None
    db.session.commit()

    return redirect(url_for("auth.login",
                            success="Email verified! You can now log in."))


# ── RESEND VERIFICATION ───────────────────────────────────

@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    email = request.form.get("email", "").strip().lower()
    user  = User.query.filter_by(email=email).first()

    if user and not user.is_verified:
        send_verification_email(user)
        session["pending_email"] = email

    return render_template("verify_email.html",
                           email=email,
                           success="A new verification link has been sent.")


# ── LOGIN ─────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    success_msg = request.args.get("success", "")

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember")

        user = User.query.filter_by(email=email).first()

        if not user or not bcrypt.check_password_hash(user.password, password):
            return render_template("login.html",
                                   error="Incorrect email or password.")

        if not user.is_verified:
            session["pending_email"] = email
            return redirect(url_for("auth.verify_pending"))

        session["user_id"]    = user.id
        session["user_email"] = user.email
        session.permanent     = bool(remember)
        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html", success=success_msg)


# ── LOGOUT ────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))