# AI-Powered Heart Sound Disease Detection System
### Full-Stack Django + Machine Learning + AI Healthcare Chatbot

---

## 1. Project Overview

**HeartSound AI** is an advanced, full-stack medical acoustic research and screening web platform. The system ingests phonocardiogram (PCG) heart sound recordings via audio upload or real-time browser microphone capture, processes the signal with Librosa, extracts a 190-dimensional feature vector, and classifies the sound into **Normal** or **Abnormal** categories using a trained Scikit-learn model.

The platform provides a responsive, animated medical dashboard, interactive audio playback and spectrogram visual plots, downloadable ReportLab PDF medical screening reports, a validated symptom questionnaire, and a conversational **HeartCare AI Assistant** with built-in emergency detection.

---

## 2. Key Features

- **Separated User & Admin Portals:** Distinct User Portal (`/accounts/login/`, `/dashboard/`) and dedicated Administrative Control Panel (`/admin-portal/login/`, `/admin-portal/dashboard/`).
- **Administrative Control Panel:** Full management of users, heart-sound analyses, symptom assessments, clinical reports, HeartCare AI conversations, model architecture, and security audit logs.
- **Role-Based Server-Side Protection:** HTTP 403 Forbidden enforcement on all administrative endpoints; zero privilege leakage.
- **6-Tab User Inspection:** Profile info, analysis history, assessments, clinical reports, chat activity, and audit trails without direct database inspection.
- **Automated Data Backup & Retention:** Automated timestamped SQLite backups with configurable retention cleanup via `python manage.py backup_data`.
- **In-App Notification Center:** Real-time event notifications for completed screenings, high-risk assessments, and system alerts.
- **Dark & Light Mode Engine:** Real-time theme toggling with localStorage persistence across both portals.
- **User Authentication & Privacy:** Secure signup, login, password change, account deletion request, session timeout, profile management, and granular user-isolated data permissions.
- **Audio Ingestion:** Supports WAV, FLAC, MP3, OGG, and AIFF files up to 50 MB, plus in-browser Web Audio microphone recording with live visualizer.
- **Signal Processing Pipeline:** Enforces 1.0s to 300s duration checks, 22.05 kHz resampling, mono downmixing, zero-padding/trimming to 5s windows, and peak normalization.
- **Acoustic Feature Extraction:** Computes 190 numerical features: 40 MFCCs (mean & std), 12 Chroma features, 7 Spectral Contrast bands, Spectral Centroid and Bandwidth, Zero Crossing Rate, and 64 Mel-energy bands.
- **Machine Learning Inference:** Serialized `RandomForestClassifier` with balanced class weights, feature scaling, model probability vectors, and graceful fallback when models are not loaded.
- **PDF Report Generation:** Print-ready medical screening summaries generated via ReportLab with model parameters, spectrograms, and disclaimers.
- **Symptom Risk Assessment:** 14-question cardiac evaluation tool with risk categorization (`Low`, `Moderate`, `High`, `Seek Urgent Care`).
- **HeartCare AI Assistant:** Conversational chatbot with configurable OpenAI/Gemini/Claude integrations and a built-in rule-based emergency triage fallback.
- **Administrative Governance:** Django admin console with user management, system audit logging, and model metadata tracking.

---

## 3. Technology Stack

- **Backend:** Python 3.14 & Django 6.1
- **Database:** SQLite 3 via Django ORM
- **Machine Learning:** Scikit-learn 1.9 & NumPy 2.5
- **Audio Processing:** Librosa 1.0 & SoundFile 0.14
- **Visualizations:** Matplotlib 3.11 (headless Agg) & Chart.js 4.4
- **Reporting:** ReportLab 5.1
- **UI & Animations:** Bootstrap 5.3, Bootstrap Icons, AOS (Animate on Scroll)
- **Static Assets:** WhiteNoise 6.12

---

## 4. Local Installation & Windows Setup

### Step 1: Open PowerShell in the project directory
```powershell
cd "C:\Users\kumar\OneDrive\Desktop\aditya project"
```

### Step 2: Install dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```
*(Optional: Add your `OPENAI_API_KEY`, `GEMINI_API_KEY`, or `ANTHROPIC_API_KEY` in `.env` if you want live cloud LLM chat responses. If left blank, the chatbot runs in rule-based FAQ mode).*

### Step 4: Run Database Migrations
```powershell
python manage.py migrate
```

### Step 5: Create or Initialize Administrator Account
To create a custom administrator securely:
```powershell
python manage.py createsuperuser
```
Or use the automated initial administrator generator:
```powershell
python manage.py init_admin
```
*(Default generated credentials: username `admin`, password `Admin12345!` — change immediately in production!)*

### Step 6: Automated Database Backup & Retention
To create timestamped SQLite backups:
```powershell
python manage.py backup_data --retention-days 30
```

### Step 7: Access the Dedicated Portals
- **Standard User Portal:** `http://127.0.0.1:8000/accounts/login/` &rarr; `http://127.0.0.1:8000/dashboard/`
- **Admin Control Panel:** `http://127.0.0.1:8000/admin-portal/login/` &rarr; `http://127.0.0.1:8000/admin-portal/dashboard/`

### Step 6: Verify or Retrain the Machine Learning Model
The repository includes a trained model in `ml_models/`. To retrain on datasets:
```powershell
python ml_pipeline/model_training.py --dataset_dir datasets/ --output_dir ml_models/
```

### Step 7: Run Automated Tests
```powershell
python manage.py test tests
```

### Step 8: Start the Local Development Server
```powershell
python manage.py runserver
```
Open your browser and navigate to: **`http://127.0.0.1:8000/`**

---

## 5. Folder Hierarchy

```text
ADITYA PROJECT/
├── manage.py                          # Django execution entry point
├── requirements.txt                   # Production dependency specifications
├── .env.example                       # Environment template
├── .gitignore                         # Version control exclusions
├── README.md                          # Quickstart & documentation index
├── db.sqlite3                         # Relational SQLite database
│
├── config/                            # Core project settings & URL routing
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/                          # Module 1: Auth & User Profile
│   ├── models.py, views.py, forms.py, urls.py, admin.py
├── dashboard/                         # Module 2: Animated User Dashboard
│   ├── views.py, urls.py
├── heart_analysis/                    # Module 3 & 4: Audio Ingest, Waveforms & ML Interface
│   ├── models.py, views.py, forms.py, services.py, urls.py, admin.py
├── assessments/                       # Module 7: Health Symptom Assessment
│   ├── models.py, views.py, forms.py, urls.py, admin.py
├── chatbot/                           # Module 8: HeartCare AI Assistant
│   ├── models.py, views.py, services.py, urls.py, admin.py
├── reports/                           # Module 6: ReportLab PDF Report Generator
│   ├── views.py, urls.py
├── core/                              # Base views, error pages, audit logging
│   ├── models.py, views.py, middleware.py, context_processors.py, urls.py, admin.py
│
├── ml_pipeline/                       # Module 4 & 5: Acoustic ML Pipeline
│   ├── audio_processing.py            # Resampling, normalization, waveform & spectrogram plots
│   ├── feature_extraction.py          # 190-dim MFCC, Chroma, Contrast, Mel feature vectors
│   ├── model_training.py              # Stratified split, training, cross-validation
│   ├── prediction.py                  # Standard scaler transform & inference engine
│   └── evaluation.py                  # Standalone performance report & confusion matrix
│
├── ml_models/                         # Trained model artifacts
│   ├── heart_sound_classifier.pkl     # Fitted RandomForestClassifier
│   ├── scaler.pkl                     # Fitted StandardScaler
│   ├── model_metadata.json            # Model parameters, version, & metrics
│   └── README.md
│
├── datasets/                          # Phonocardiogram datasets & generator
│   ├── generate_sample_dataset.py     # Synthetic cardiac cycle PCG generator
│   ├── normal/                        # Healthy baseline recordings
│   ├── abnormal/                      # Murmur & pathological recordings
│   └── README.md                      # PhysioNet 2016 sourcing guide
│
├── templates/                         # HTML5 Django templates
│   ├── base.html                      # Global layout, navbar, footer & chatbot pill
│   ├── home.html, about.html, how_it_works.html, help_faq.html, privacy_policy.html, terms_disclaimer.html
│   ├── accounts/ (register, login, profile, password_reset)
│   ├── dashboard/ (dashboard.html)
│   ├── heart_analysis/ (upload.html, result.html, history.html)
│   ├── assessments/ (assessment.html, result.html, history.html)
│   ├── chatbot/ (chatbot.html)
│   └── errors/ (403.html, 404.html, 500.html)
│
├── static/                            # Static assets
│   ├── css/main.css                   # Custom dark medical AI theme & animations
│   ├── js/main.js                     # Web Audio API mic recording, Chart.js, chatbot AJAX
│   └── vendor/
│
├── media/                             # Protected uploaded audio storage
│   └── heart_sounds/
│
├── tests/                             # Automated test suite
│   └── test_all.py                    # 12 comprehensive unit and integration tests
│
└── docs/                              # Formal system documentation
    ├── architecture.md                # System diagrams, ontology graph, DFDs
    ├── database_schema.md             # ER diagrams, table schemas & constraints
    ├── project_documentation.md       # Full engineering report
    └── user_manual.md                 # Operating and administration manual
```

---

## 6. Testing & Quality Assurance

All 12 automated unit and integration tests are verified:

```powershell
python manage.py test tests
```

Output:
```text
Creating test database for alias 'default'...
............
----------------------------------------------------------------------
Ran 12 tests in 5.768s

OK
Destroying test database for alias 'default'...
```

Test coverage includes:
- User registration and data consent persistence
- Unauthenticated access redirects on protected routes
- Strict cross-user data isolation
- Audio normalization, 22.05 kHz resampling, and padding
- Rejection of corrupt and silent audio
- 190-dimensional feature extraction verification
- Graceful handling of missing model files
- Symptom assessment score calculation
- Chatbot emergency phrase detection & rule-based fallback

---

## 7. Medical & Legal Disclaimer

**HeartSound AI is designed for scientific research, engineering demonstration, and screening support purposes only.** It is not certified as a medical device by the FDA, CE, or CDSCO. Classification outputs and chatbot messages must never replace consultation with a qualified physician or cardiologist. In case of acute chest pain, shortness of breath, or collapse, contact emergency medical services immediately.
