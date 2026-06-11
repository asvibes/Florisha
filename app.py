import os
from flask import Flask, render_template, redirect, url_for, session, send_from_directory
from datetime import timedelta

from extensions import db, migrate, bcrypt, mail
from config import Config
from models.user import User
from models.plant import Plant
from models.journal_entry import JournalEntry          # ← new
from routes.dashboard import dashboard_bp
from routes.ai_routes import ai_bp
from routes.auth_routes import auth_bp
from routes.journal_routes import journal_bp           # ← new
from routes.calendar_routes import calendar_bp   # missing import
       
app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(calendar_bp)     # missing registration  
db.init_app(app)
migrate.init_app(app, db)
bcrypt.init_app(app)
mail.init_app(app)

app.register_blueprint(dashboard_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(journal_bp)                     # ← new

app.permanent_session_lifetime = timedelta(days=30)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/start")
def start():
    if "user_id" in session:
        return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("ai.identify_page"))


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    upload_folder = os.path.abspath(app.config["UPLOAD_FOLDER"])
    return send_from_directory(upload_folder, filename)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)