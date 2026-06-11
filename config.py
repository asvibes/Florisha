import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Core
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    # PlantNet
    PLANTNET_API_KEY = "2b104P6k2P7lUb9CRpFYnip7xO"
    PLANTNET_API_URL = "https://my-api.plantnet.org/v2/identify/all"

    # Gmail SMTP
    MAIL_SERVER   = "smtp.gmail.com"
    MAIL_PORT     = 587
    MAIL_USE_TLS  = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")