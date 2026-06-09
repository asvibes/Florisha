#  Flourisha

Flourisha is a web-based flora identification platform that helps users identify plants, flowers, trees, shrubs, leaves, and other botanical species through image recognition.

Users can upload an image and receive species predictions, botanical information, and related species recommendations, making plant discovery simple and educational.

---

##  Features

###  Flora Identification

* Upload images of plants, flowers, trees, shrubs, and leaves.
* Identify species using the Pl@ntNet API.
* View confidence scores and alternative matches.

### Species Information

* Common name
* Scientific name
* Family classification
* Genus classification
* Description and characteristics
* Habitat information

###  Related Species Recommendations

* Discover botanically related species.
* Recommendations based on genus and family relationships.

###  User Accounts

* Registration and login functionality.
* Secure session management using Flask-Login.
* Personalized identification history.

###  Identification History

* Save previous identifications.
* Review uploaded images and results.
* Re-identify previously uploaded images.
* Delete history records.

###  Guest Mode

* Identify flora without creating an account.
* Guest images are automatically deleted after processing.

---

##  Tech Stack

### Frontend

* HTML
* CSS
* JavaScript

### Backend

* Flask

### Database

* MySQL

### Authentication

* Flask-Login

### Identification Service

* Pl@ntNet API

### Storage

* Local file storage (`uploads/`)

---

## Project Structure

```text
Flourisha/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│
├── uploads/
│
├── instance/
│
├── app.py
├── models.py
├── requirements.txt
├── .env
└── README.md
```

## Getting Started

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Flourisha
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate:

Windows

```bash
.venv\Scripts\activate
```

Linux/macOS

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```env
SECRET_KEY=your_secret_key

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=flourisha

PLANTNET_API_KEY=your_api_key
```

### 5. Run the Application

```bash
python app.py
```

Visit:

```text
http://127.0.0.1:5000
```

---

## Database

### Users

Stores account information.

### Species

Stores identified flora information.

### Identification History

Stores user identification records.

### Uploaded Files

Stores image metadata and file locations.

---

##  Security

* Password hashing
* Session-based authentication
* Protected routes
* Upload validation
* Environment variable configuration

---


---

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature-name
```

3. Commit changes

```bash
git commit -m "Add feature"
```

4. Push branch

```bash
git push origin feature-name
```

5. Open a Pull Request

---


---

## About

Flourisha was created to make flora identification simple, educational, and accessible. By combining image recognition with botanical information, the platform helps users explore and learn about the natural world.
