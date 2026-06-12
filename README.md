# 🌿 Florisha

> **Your intelligent plant companion** — identify, learn, and care for plants with the power of AI.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-florisha--8--1vd3.onrender.com-brightgreen)](https://florisha-8-1vd3.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.14-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-lightgrey)](https://flask.palletsprojects.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI-orange)](https://ai.google.dev/)

---

| Home |
|------|
| <img width="1535" height="720" alt="image" src="https://github.com/user-attachments/assets/8612b907-f7fb-479f-9c4e-a61b4da31a2d" /> |

| Dashboard |
|-----------|
| <img width="1530" height="727" alt="image" src="https://github.com/user-attachments/assets/d3a814e5-6a19-4d43-9945-9a4c198c7094" /> |

| Plant Identification |
|----------------------|
| <img width="1536" height="721" alt="image" src="https://github.com/user-attachments/assets/ec8093fa-d520-4e06-a63d-92715ca9b69a" /> |

| Result |
|--------| 
| <img width="1531" height="717" alt="image" src="https://github.com/user-attachments/assets/ac36d76d-06f4-4e86-8260-a24e53dc04f5" /> |

| Favourite |
|-----------|
|<img width="1532" height="717" alt="image" src="https://github.com/user-attachments/assets/e4f4e5b3-37c3-49f4-bbd0-0067794e2509" /> |

| Journal | 
|---------|
| <img width="1536" height="717" alt="image" src="https://github.com/user-attachments/assets/c1c3bc8e-b850-44e6-a99e-c53d41c0b637" /> |

| Calendar|
|---------|
|<img width="1532" height="718" alt="image" src="https://github.com/user-attachments/assets/3b0704f9-25ce-4336-a8ab-0004c1c2e75b" /> |

---

## ✨ Features

- **🔍 Plant Identification** — Upload a photo and identify any plant instantly using the PlantNet API
- **📓 Plant Journal** — Save and revisit your identified plants with personal notes
- **📅 Care Calendar** — Track watering and care schedules with a visual calendar
- **🔐 Secure Auth** — Email verification, bcrypt password hashing, and session management
- **🌱 Personalised Dashboard** — View your plant collection, favourites, and journal entries in one place

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.14, Flask 3.0 |
| Database | PostgreSQL (via SQLAlchemy + psycopg2) |
| ORM & Migrations | Flask-SQLAlchemy, Flask-Migrate (Alembic) |
| AI — Plant Profiles | Google Gemini 2.0 Flash (`google-genai`) |
| Plant Identification | PlantNet API |
| Email | Brevo (Sendinblue) Transactional API |
| Auth | Flask-Login, Flask-Bcrypt |
| ML | scikit-learn (`model.pkl`) |
| Frontend | Jinja2 Templates, HTML/CSS/JS |
| Server | Gunicorn |
| Deployment | Render |

---

## 📁 Project Structure

```
Florisha/
│
├── app.py                         # App entry point
├── config.py                      # Configuration & environment variables
├── extensions.py                  # Flask extensions (db, bcrypt, mail)
├── planet_knowledge.py            # Plant domain knowledge base & facts
├── plant_service.py               # Core plant service layer (business logic)
├── requirements.txt               # Python dependencies
├── runtime.txt                    # Python version for Render
├── .python-version                # Local Python version
├── .env                           # Environment variables (not committed)
├── .gitignore
│
├── models/                        # SQLAlchemy database models
│   ├── __init__.py
│   ├── user.py
│   ├── plant.py
│   ├── journal_entry.py
│   └── calendar_preferences.py
│
├── routes/                        # Flask Blueprints
│   ├── __init__.py
│   ├── auth_routes.py             # Register, login, logout, email verification
│   ├── ai_routes.py               # Plant identification & AI profile generation
│   ├── dashboard.py               # User dashboard
│   ├── main_routes.py             # Home & static pages
│   ├── journal_routes.py          # Plant journal CRUD
│   └── calendar_routes.py         # Care calendar
│
├── services/                      # External API integrations
│   ├── gemini_service.py          # Google Gemini AI plant profiles
│   └── plant_processor.py         # PlantNet identification processing
│
├── modules/                       # AI & recommendation logic
│   ├── ai_engine.py
│   ├── prompt_engine.py
│   ├── recommendation.py
│   └── user_profile.py
│
├── ml/
│   └── model.pkl                  # Trained ML model
│
├── utils/
│   ├── image_handler.py           # Image upload & processing
│   └── cloudinary_helper.py       # Cloudinary cloud image storage helper
│
├── static/                        # CSS, JS, Images
│   ├── css/style.css
│   ├── js/app.js
│   └── images/
│
├── templates/                     # Jinja2 HTML templates
│   ├── index.html
│   ├── dashboard.html
│   ├── identify.html
│   ├── result.html
│   ├── chat.html
│   ├── login.html
│   ├── register.html
│   ├── verify_email.html
│   ├── forgot_password.html
│   ├── reset_password.html
│   └── upload.html
│
├── migrations/                    # Alembic database migrations
│   ├── versions/
│   ├── alembic.ini
│   ├── env.py
│   ├── README.md
│   └── script.py.mako
│
├── data/                          # JSON data files
│   ├── users.json
│   └── history.json
│
└── uploads/                       # User uploaded plant images
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Google Gemini API key
- PlantNet API key
- Brevo (Sendinblue) API key

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/asvibes/Florisha.git
cd Florisha
```

2. **Create a virtual environment**
```bash
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create a `.env` file** in the root directory:
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@host:5432/dbname
GEMINI_API_KEY=your-gemini-api-key
PLANTNET_API_KEY=your-plantnet-api-key
BREVO_API_KEY=your-brevo-api-key
MAIL_USERNAME=your-email@gmail.com
```

5. **Run database migrations**
```bash
flask db upgrade
```

6. **Start the development server**
```bash
flask run
```

Visit `http://localhost:5000` in your browser.

---

## ☁️ Deployment (Render)

Florisha is deployed on [Render](https://render.com).

### Environment Variables (set in Render dashboard)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (auto-set by Render) |
| `SECRET_KEY` | Flask secret key for sessions |
| `GEMINI_API_KEY` | Google AI Studio API key |
| `PLANTNET_API_KEY` | PlantNet identification API key |
| `BREVO_API_KEY` | Brevo transactional email API key |

### Start Command
```
gunicorn app:app
```

---

## 🔑 API Keys

| Service | Where to get it | 
|---------|----------------|
| Google Gemini | [aistudio.google.com](https://aistudio.google.com) |
| PlantNet | [my-api.plantnet.org](https://my-api.plantnet.org) |
| Brevo Email | [brevo.com](https://brevo.com) |

---

## 🌱 How It Works

1. **User uploads a photo** of a plant on the dashboard
2. **PlantNet API** identifies the plant species with confidence scores
3. **Results are saved** to the user's journal and plant collection
4. **Users can chat** with the AI about their plants, set care reminders, and track watering schedules

---

## 📄 License

This project is for educational and personal use.

---

## 👩‍💻 Author

Built with 💚 by **Shreya** — [@asvibes](https://github.com/asvibes)

---

*Florisha — because every plant deserves to be known.* 🌿
