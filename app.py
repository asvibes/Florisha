import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
from datetime import timedelta

from extensions import db, migrate
from config import Config
from models.user import User
from models.plant import Plant
from routes.dashboard import dashboard_bp
from routes.ai_routes import ai_bp

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate.init_app(app, db)

app.register_blueprint(dashboard_bp)
app.register_blueprint(ai_bp)

app.permanent_session_lifetime = timedelta(days=30)


# ──────────────────── HOME ────────────────────
@app.route("/")
def home():
    return render_template("index.html")


# ──────────────────── START ───────────────────
@app.route("/start")
def start():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("ai.identify_page"))   # guests → standalone identify page


# ──────────────────── UPLOADS ─────────────────
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    upload_folder = os.path.abspath(app.config["UPLOAD_FOLDER"])
    return send_from_directory(upload_folder, filename)


# ──────────────────── LOGIN ───────────────────
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember")

        user = User.query.filter_by(email=email, password=password).first()

        if user:
            session["user_id"]    = user.id
            session["user_email"] = user.email
            session.permanent     = bool(remember)
            return redirect(url_for("dashboard.dashboard"))

        return render_template("login.html",
                               error="Incorrect email or password. Please try again.")

    return render_template("login.html")


# ──────────────────── REGISTER ────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email            = request.form.get("email", "").strip()
        password         = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not email or not password or not confirm_password:
            return render_template("register.html",
                                   error="All fields are required.")

        if password != confirm_password:
            return render_template("register.html",
                                   error="Passwords do not match. Please try again.")

        if len(password) < 6:
            return render_template("register.html",
                                   error="Password must be at least 6 characters.")

        existing = User.query.filter_by(email=email).first()
        if existing:
            return render_template("register.html",
                                   error="An account with that email already exists.")

        new_user = User(email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")


# ──────────────────── LOGOUT ──────────────────
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ──────────────────── RUN ─────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)