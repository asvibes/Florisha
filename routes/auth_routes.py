import os
import secrets
from datetime import datetime, timedelta

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from flask import (Blueprint, render_template, redirect,
                   url_for, session, request, flash)
from extensions import db, bcrypt
from models.user import User

auth_bp = Blueprint("auth", __name__)


# ── helpers ──────────────────────────────────────────────

def send_verification_email(user):
    if not user.email or '@' not in user.email:
        raise ValueError(f"Invalid email address: '{user.email}'")

    token  = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=1)

    user.verification_token = token
    user.token_expiry       = expiry
    db.session.commit()

    link = url_for("auth.verify_email", token=token, _external=True)

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": user.email}],
        sender={"email": "florisha.app@gmail.com", "name": "Florisha"},
        subject="Verify your Florisha account",
        text_content=(
            f"Hi,\n\n"
            f"Thanks for joining Florisha! Click the link below to verify "
            f"your email address. This link expires in 1 hour.\n\n"
            f"{link}\n\n"
            f"If you didn't create an account, you can ignore this email.\n\n"
            f"— The Florisha Team"
        )
    )

    try:
        api_instance.send_transac_email(email)
    except ApiException as e:
        print(f"[Brevo] Failed to send verification to '{user.email}': {e}")
        raise


def send_reset_email(user):
    if not user.email or '@' not in user.email:
        raise ValueError(f"Invalid email address: '{user.email}'")

    token  = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(hours=1)

    user.reset_token        = token
    user.reset_token_expiry = expiry
    db.session.commit()

    link = url_for("auth.reset_password", token=token, _external=True)

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY")

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    email = sib_api_v3_sdk.SendSmtpEmail(
        to=[{"email": user.email}],
        sender={"email": "florisha.app@gmail.com", "name": "Florisha"},
        subject="Reset your Florisha password",
        text_content=(
            f"Hi,\n\n"
            f"We received a request to reset your Florisha password. "
            f"Click the link below to choose a new one. This link expires in 1 hour.\n\n"
            f"{link}\n\n"
            f"If you didn't request a password reset, you can safely ignore this email — "
            f"your password will not be changed.\n\n"
            f"— The Florisha Team"
        )
    )

    try:
        api_instance.send_transac_email(email)
    except ApiException as e:
        print(f"[Brevo] Failed to send reset email to '{user.email}': {e}")
        raise


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

        try:
            send_verification_email(new_user)
        except Exception as e:
            print(f"[Register] Email send failed for {email}: {e}")
            return render_template("register.html",
                                   error="Account created but we couldn't send the verification email. "
                                         "Please use 'Resend' on the next page.")

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

    if not email:
        return render_template("verify_email.html", email="",
                               error="Email address is missing. Please go back and try registering again.")

    user = User.query.filter_by(email=email).first()

    if user and not user.is_verified:
        try:
            send_verification_email(user)
            session["pending_email"] = email
        except Exception as e:
            print(f"[Resend] Email send failed for {email}: {e}")
            return render_template("verify_email.html", email=email,
                                   error="Failed to send verification email. Please try again in a moment.")

    return render_template("verify_email.html",
                           email=email,
                           success="A new verification link has been sent.")


# ── FORGOT PASSWORD ───────────────────────────────────────

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not email:
            return render_template("forgot_password.html",
                                   error="Please enter your email address.")

        user = User.query.filter_by(email=email).first()

        if user and user.is_verified:
            try:
                send_reset_email(user)
            except Exception as e:
                print(f"[ForgotPassword] Email send failed for {email}: {e}")
                return render_template("forgot_password.html",
                                       error="Something went wrong sending the email. Please try again.")

        # Always show same message — prevents email enumeration
        return render_template("forgot_password.html",
                               success="If that email is registered, you'll receive a reset link shortly.")

    return render_template("forgot_password.html")


# ── RESET PASSWORD ────────────────────────────────────────

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()

    if not user:
        return render_template("reset_password.html",
                               error="This reset link is invalid or has already been used.",
                               token=None)

    if datetime.utcnow() > user.reset_token_expiry:
        return render_template("reset_password.html",
                               error="This reset link has expired. Please request a new one.",
                               token=None)

    if request.method == "POST":
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password or not confirm_password:
            return render_template("reset_password.html",
                                   error="Both fields are required.", token=token)

        if len(password) < 6:
            return render_template("reset_password.html",
                                   error="Password must be at least 6 characters.", token=token)

        if password != confirm_password:
            return render_template("reset_password.html",
                                   error="Passwords do not match.", token=token)

        user.password           = bcrypt.generate_password_hash(password).decode("utf-8")
        user.reset_token        = None
        user.reset_token_expiry = None
        db.session.commit()

        return redirect(url_for("auth.login",
                                success="Password updated! You can now log in with your new password."))

    return render_template("reset_password.html", token=token)


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