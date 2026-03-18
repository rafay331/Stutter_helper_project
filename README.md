# Stutter Helper Project

Stutter Helper Project is a Flask web application for speech therapy support. It brings together patient-facing speech tools, therapist monitoring workflows, parent progress views, audio processing, dysarthria prediction, and report/export utilities in one system.

## Features

- User registration, login, profile management, and Google OAuth
- Role-based flows for patients, therapists, and parents
- Audio upload, recording, playback, deletion, and conversion
- Whisper-based speech transcription
- Text cleanup and text-to-speech generation
- Audio enhancement for uploaded and recorded speech
- Dysarthria prediction using bundled trained model files
- Therapist notes, speech exercise assignment, and submission review
- Parent monitoring dashboard and report export
- User and feedback export utilities

## Tech Stack

- Python
- Flask
- MySQL
- Flask-Bcrypt
- Flask-Dance
- OpenAI Whisper
- librosa, soundfile, scipy, psola
- scikit-learn, joblib
- openpyxl, reportlab

## Project Structure

```text
FYP_V2/
|-- main.py
|-- requirements.txt
|-- .env
|-- .env.example
|-- audio_enhance.py
|-- dysarthria_inference.py
|-- templates/
|-- uploads/
|-- audio_uploads/
|-- archives/
|-- *.joblib
```

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/rafay331/Stutter_helper_project.git
cd Stutter_helper_project
```

If your cloned repo opens at the project root directly, run commands there. If your local copy matches this workspace layout, use the inner `FYP_V2` folder that contains `main.py`.

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your local values.

Required variables:

```env
SECRET_KEY=your_secret_key
GOOGLE_OAUTH_CLIENT_ID=your_google_client_id
GOOGLE_OAUTH_CLIENT_SECRET=your_google_client_secret
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=login
FLASK_DEBUG=1
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

## Database Notes

The app expects a MySQL database named `login` and references tables such as:

- `login`
- `users`
- `uploaded_audio`
- `stutter_removed_audio`
- `therapist_notes`
- `speech_exercises`
- `speech_assignments`
- `speech_submissions`

## Run

From the folder containing `main.py`:

```bash
python main.py
```

Default local URL:

```text
http://127.0.0.1:5000
```

## Main Pages

- `/`
- `/login`
- `/register`
- `/profile`
- `/ui`
- `/results`
- `/therapist_dashboard`
- `/parent_monitor`
- `/user_management`
