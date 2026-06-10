import os

class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:20shreya07@localhost/florisha_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "change-this-to-a-secure-random-key"

    # uploads
    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024          # 16 MB max upload size
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    # Pl@ntNet
    PLANTNET_API_KEY = "2b104P6k2P7lUb9CRpFYnip7xO"       # ← paste your key here
    PLANTNET_API_URL = "https://my-api.plantnet.org/v2/identify/all"