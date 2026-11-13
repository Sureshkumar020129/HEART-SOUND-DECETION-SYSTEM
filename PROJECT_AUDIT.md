# HeartSound AI — Project Audit Report (PHASE 1)

**Project Name:** AI-Powered Heart Sound Disease Detection System (HeartSound AI)  
**Inspection Date:** November 13, 2026  
**Auditor:** Senior Full-Stack Django Developer & ML Systems Engineer  
**Workspace:** `C:\Users\kumar\OneDrive\Desktop\aditya project`  
**Primary Stack:** Django 6.1.3, Python 3.14, SQLite 3, Scikit-learn 1.9.1, Librosa 1.0.0, ReportLab 5.1.0, Bootstrap 5.3.2  

---

## 1. Executive Summary

HeartSound AI is a mature, custom-built Django web application for phonocardiogram (PCG) acoustic screening and cardiovascular symptom risk assessment. The project features separated user and administrator portals, a functional Librosa-to-Scikit-learn acoustic feature extraction pipeline, a multi-provider conversational AI chatbot with emergency triage, ReportLab PDF clinical report exports, and an in-app notification center.

The application is largely functional; however, critical gaps exist around incomplete media backup routines, placeholder secret keys, a stubbed administrative model evaluation endpoint, orphaned plot image cleanup, and a machine learning model that was trained solely on 30 synthetic audio samples rather than a clinical dataset.

This audit report documents the exact state of all 18 functional domains without altering existing code or database records.

---

## 2. Comprehensive Directory & File Structure

```text
C:\Users\kumar\OneDrive\Desktop\aditya project\
├── .env                              # Environment configuration (active)
├── .env.example                      # Template configuration
├── .gitignore                        # Git exclusion rules
├── db.sqlite3                        # Active SQLite 3 database (290 KB, 5 user records)
├── manage.py                         # Django management entry point
├── README.md                         # Documentation & run instructions
├── requirements.txt                  # Python dependencies
│
├── accounts/                         # Application: User authentication & profile
│   ├── forms.py                      # RegistrationForm, CustomLoginForm, UserProfileForm
│   ├── models.py                     # UserProfile (role, status, consent, phone, avatar)
│   ├── urls.py                       # User auth routes (/accounts/login/, register/, etc.)
│   ├── views.py                      # Auth handlers & profile logic
│   └── migrations/                   # 0001_initial, 0002_userprofile_status...
│
├── admin_portal/                     # Application: Dedicated Admin Control Panel
│   ├── decorators.py                 # @admin_required enforcing 403 Forbidden
│   ├── forms.py                      # AdminLoginForm, AdminUserEditForm, SiteConfigurationForm
│   ├── urls.py                       # Admin routing (/admin-portal/dashboard/, users/, etc.)
│   ├── views.py                      # 748 lines of comprehensive admin management views
│   └── migrations/                   # App migrations
│
├── assessments/                      # Application: Cardiovascular symptom questionnaire
│   ├── forms.py                      # HealthAssessmentForm (14 clinical questions)
│   ├── models.py                     # HealthAssessment model with rule-based risk scoring
│   ├── urls.py                       # Routes (/assessment/, history/, result/)
│   ├── views.py                      # Questionnaire submission & scoring views
│   └── migrations/                   # 0001_initial
│
├── backups/                          # Automated SQLite database backups
│   ├── db_backup_20261112_235539.sqlite3
│   └── db_backup_20261113_000024.sqlite3
│
├── chatbot/                          # Application: HeartCare AI Assistant
│   ├── models.py                     # ChatSession & ChatMessage
│   ├── services.py                   # OpenAI, Gemini, Claude calls, emergency regex, FAQ fallback
│   ├── urls.py                       # Chatbot interface & AJAX API endpoints
│   ├── views.py                      # Session handling & message dispatch
│   └── migrations/                   # 0001_initial
│
├── config/                           # Django Project Configuration
│   ├── asgi.py                       # ASGI configuration
│   ├── settings.py                   # 316 lines of core settings & security configuration
│   ├── urls.py                       # Root URL dispatcher
│   └── wsgi.py                       # WSGI entry point
│
├── core/                             # Application: Core layouts, governance & audit
│   ├── context_processors.py         # Global site_context (notifications, branding, roles)
│   ├── middleware.py                 # AuditLogMiddleware (client IP tracking & 403 capture)
│   ├── models.py                     # AuditLog, SiteConfiguration, Notification
│   ├── urls.py                       # Landing page, informational pages, notifications
│   ├── views.py                      # Home, about, how-it-works, notification endpoints
│   ├── management/commands/          # Management commands
│   │   ├── backup_data.py            # SQLite database backup & retention pruner
│   │   └── init_admin.py             # Default superuser initialization
│   └── migrations/                   # 0001_initial, 0002_notification
│
├── dashboard/                        # Application: User Analytics Dashboard
│   ├── urls.py                       # /dashboard/ route
│   ├── views.py                      # User KPI metrics, 14-day trend charts
│   └── tests.py                      # Dashboard UI integration tests
│
├── datasets/                         # PCG Audio Datasets
│   ├── README.md                     # PhysioNet / CinC Challenge 2016 setup instructions
│   ├── generate_sample_dataset.py    # Synthetic PCG generator (normal & abnormal)
│   ├── normal/                       # 15 synthetic normal WAV files (220.5 KB each)
│   └── abnormal/                     # 15 synthetic abnormal WAV files (220.5 KB each)
│
├── heart_analysis/                   # Application: Heart Sound Analysis & Ingestion
│   ├── forms.py                      # AudioUploadForm
│   ├── models.py                     # HeartSoundRecording, AnalysisRecord, PredictionResult, ModelMetadata
│   ├── services.py                   # run_analysis orchestrator (audio processing -> ML inference)
│   ├── urls.py                       # Analysis routing (/analysis/upload/, record/, history/)
│   ├── views.py                      # Upload, Web Audio record, results, and deletion
│   └── migrations/                   # 0001_initial, 0002_alter_heartsoundrecording...
│
├── media/                            # User Uploaded & Generated Media Files
│   ├── analysis_plots/               # Waveform and spectrogram PNG output plots
│   └── heart_sounds/                 # User uploaded audio partitioned by user ID (2/, 3/, 4/, 5/)
│
├── ml_models/                        # Machine Learning Model Artifacts
│   ├── heart_sound_classifier.pkl    # Serialized RandomForestClassifier (105,329 bytes)
│   ├── scaler.pkl                    # Serialized StandardScaler (4,968 bytes)
│   ├── model_metadata.json           # Model configuration, parameters, and metrics
│   └── README.md                     # Model training & architecture documentation
│
├── ml_pipeline/                      # ML Signal Processing Pipeline
│   ├── audio_processing.py           # Audio loading, resampling (22.05kHz), normalization, plots
│   ├── feature_extraction.py         # 190-dimensional feature extraction (MFCC, Chroma, Mel, etc.)
│   ├── model_training.py             # RandomForest training script with cross-validation
│   ├── evaluation.py                 # Standalone model evaluation & classification report
│   └── prediction.py                 # Inference service with graceful failure handling
│
├── reports/                          # Application: PDF Report Generation
│   ├── urls.py                       # /reports/<pk>/download/ route
│   ├── views.py                      # ReportLab PDF generator (A4, tables, disclaimers)
│   └── migrations/                   # App migrations
│
├── static/                           # Static Assets (Source)
│   ├── css/main.css                  # Custom styling, dark/light theme variables, healthcare CSS
│   ├── js/main.js                    # Theme toggle, drag-and-drop upload, AOS init
│   ├── images/                       # Brand and healthcare imagery
│   └── vendor/                       # Third-party assets
│
├── staticfiles/                      # WhiteNoise collected static assets
├── templates/                        # Global and app HTML templates (Bootstrap 5.3)
└── tests/                            # Automated test suite
    └── test_all.py                   # 319 lines of automated unit and integration tests
```

---

## 3. Analysis of the 18 Project Domains

### 3.1 Django Applications & Responsibilities
The project is modularized into 8 dedicated Django applications:
- **`core`**: Base layouts, static informational pages, `SiteConfiguration` (singleton), `AuditLog`, `Notification`, client IP resolution, and HTTP error views (`403`, `404`, `500`).
- **`accounts`**: User lifecycle (registration, login, logout, profile updates, password change/reset) and extended `UserProfile` handling role and status.
- **`dashboard`**: Patient dashboard presenting screening metrics, recent activity, and a 14-day analysis volume trend.
- **`heart_analysis`**: Heart sound ingestion (file upload & Web Audio browser recording), signal preprocessing, visualization, feature extraction, and prediction orchestration.
- **`assessments`**: 14-question symptom risk assessment with a deterministic clinical risk engine (`low`, `moderate`, `high`, `seek_urgent`).
- **`chatbot`**: HeartCare AI Assistant supporting OpenAI, Google Gemini, Anthropic Claude, and rule-based fallback with emergency symptom detection.
- **`reports`**: Clinical screening PDF generation using ReportLab.
- **`admin_portal`**: Dedicated Administrative Control Panel with user, analysis, assessment, report, chatbot, audit, and model management.

### 3.2 Django Settings, URLs, Views, Models & Forms
- **Settings (`config/settings.py`)**: Well-structured with environment variable decoupling via `python-dotenv`. Uses WhiteNoise for static assets, dj-database-url for PostgreSQL fallback, custom password validators, and session security cookies.
- **URLs (`config/urls.py`)**: Root router delegating cleanly to each sub-application with namespacing (`accounts:`, `admin_portal:`, `heart_analysis:`, etc.).
- **Models**: Standard Django ORM with UUID primary keys on sensitive records (`HeartSoundRecording`, `AnalysisRecord`, `ChatSession`), foreign key constraints with `CASCADE` or `SET_NULL`, and meta indexing.
- **Forms**: Clean validation with Bootstrap class widget injection in `forms.py` files across all apps.

### 3.3 HTML Templates & Template Inheritance
- Base templates: `templates/base.html` (User Portal) and `templates/admin_portal/base_admin.html` (Admin Portal).
- Template inheritance (`{% extends 'base.html' %}`) is consistently utilized across all modules.
- Modern UI features: Toast messages, notification bell dropdown, theme switch buttons, and responsive modal dialogs.

### 3.4 CSS, JavaScript & Frontend Components
- **Frameworks**: Bootstrap 5.3.2, Bootstrap Icons 1.11.3, AOS (Animate On Scroll) 2.3.4, Chart.js 4.4.1.
- **Theme Engine**: Real-time Dark/Light mode engine via `data-bs-theme` attribute and `localStorage.getItem('hs_theme')`. An inline `<head>` script prevents FOUC (flash of unstyled content).
- **Audio Capture**: Browser microphone recording implemented in `heart_analysis/upload.html` via the native Web Audio `MediaRecorder` API with an animated recording canvas.

### 3.5 Database Structure & Relationships
Database engine: SQLite 3 (`db.sqlite3`).
- `accounts_userprofile` &rarr; OneToOne with `auth_user`.
- `heart_analysis_heartsoundrecording` &rarr; ForeignKey to `auth_user`.
- `heart_analysis_analysisrecord` &rarr; ForeignKey to `auth_user`, ForeignKey to `HeartSoundRecording`.
- `heart_analysis_predictionresult` &rarr; OneToOne with `AnalysisRecord`.
- `assessments_healthassessment` &rarr; ForeignKey to `auth_user`.
- `chatbot_chatsession` &rarr; ForeignKey to `auth_user`.
- `chatbot_chatmessage` &rarr; ForeignKey to `ChatSession`.
- `core_auditlog` &rarr; ForeignKey to `auth_user` (`SET_NULL`).
- `core_notification` &rarr; ForeignKey to `auth_user`.
- `core_siteconfiguration` &rarr; Singleton row (enforced in `save()`).
- `heart_analysis_modelmetadata` &rarr; Model metadata table (currently unpopulated).

### 3.6 Authentication, Registration & Session Security
- Standard User Portal at `/accounts/login/` and `/accounts/register/`.
- Password change and token-based password reset workflows are implemented.
- Automatic UserProfile creation via `post_save` Django signals.
- Role (`user`, `admin`) and Status (`active`, `inactive`, `suspended`) flags.
- Inactive/suspended user accounts are blocked during authentication.

### 3.7 User & Admin Dashboards
- **User Dashboard (`/dashboard/`)**: Displays personal KPIs (total analyses, recent screenings, normal vs abnormal breakdown, latest symptom risk), recent activity list, and 14-day analysis volume chart.
- **Admin Dashboard (`/admin-portal/dashboard/`)**: Displays system-wide metrics (total users, active/suspended ratios, total analyses, normal/abnormal/uncertain counts, total assessments, chat sessions), recent user signups, recent analyses, and 14-day registration and analysis trend charts.

### 3.8 Audio Upload & Validation Functionality
- **File Upload (`heart_analysis/views.py:upload_view`)**: Validates MIME types (`audio/wav`, `audio/mpeg`, etc.) and extensions (`.wav`, `.flac`, `.mp3`, `.ogg`, `.aiff`, `.webm`).
- **File Size Limit**: Configurable via `MAX_AUDIO_UPLOAD_MB` (default 50 MB).
- **Duration Limits**: Signal validation in `load_and_validate_audio` enforces a minimum duration of 1.0 second and a maximum of 300.0 seconds (5 minutes).
- **Silence & Corrupted Audio Rejection**: Validated with zero-vector checks and decode exception traps.

### 3.9 Audio Preprocessing & Feature Extraction
- **Audio Processing (`ml_pipeline/audio_processing.py`)**:
  - Resampling to `TARGET_SR = 22,050 Hz`.
  - Stereo-to-mono downmixing.
  - Peak amplitude normalization to `[-1.0, 1.0]`.
  - Zero-padding or center-trimming to 5.0-second standard evaluation windows.
  - Generates Base64/PNG waveform and Mel-spectrogram images via headless Matplotlib (`Agg`).
- **Feature Extraction (`ml_pipeline/feature_extraction.py`)**:
  - Concatenates 190 acoustic features:
    - 40 MFCC mean + 40 MFCC standard deviation (80 features)
    - 12 Chroma mean + 12 Chroma standard deviation (24 features)
    - 7 Spectral Contrast mean + 7 Spectral Contrast standard deviation (14 features)
    - Spectral Centroid & Bandwidth mean + std (4 features)
    - Zero-Crossing Rate & RMS energy mean + std (4 features)
    - 64 Mel-filterbank energy band means (64 features)

### 3.10 Machine Learning Model Training & Prediction
- **Architecture**: `RandomForestClassifier` with 200 trees, balanced class weights, and a fitted `StandardScaler`.
- **Inference (`ml_pipeline/prediction.py`)**:
  - Loads serialized pickle files dynamically.
  - Returns classification (`normal` or `abnormal`), probability confidence score, raw probability dictionary, and audit disclaimer.
  - **Graceful Failure**: If model files are missing or unreadable, raises `ModelNotAvailableError` and returns `status='model_unavailable'` without throwing unhandled 500 errors.

### 3.11 Model Files, Scalers & Configuration
- `ml_models/heart_sound_classifier.pkl`: Active RandomForest classifier model (105,329 bytes).
- `ml_models/scaler.pkl`: Active StandardScaler model (4,968 bytes).
- `ml_models/model_metadata.json`: Records parameters and metrics.
- **Truthful Audit Finding**: The existing model was trained on **30 synthetic audio files** generated by `generate_sample_dataset.py` (24 training samples, 6 test samples). The reported 100% test F1-score reflects this synthetic toy dataset, not clinical validation on real-world patients.

### 3.12 Patient History & Medical Records
- Users can review past analyses at `/analysis/history/` and past symptom assessments at `/assessment/history/`.
- Strict user data isolation: All queries filter on `user=request.user`. Attempting to access another user's analysis ID raises HTTP 404.

### 3.13 Doctor Review & Report Management
- **Existing**: Admin can view user assessment details and analysis parameters.
- **Missing**: There is currently no dedicated `DoctorNote` or `ClinicalReview` model where a physician can sign off, confirm, or amend an ML screening classification.
- **Admin Stub**: `report_regenerate_view` in `admin_portal/views.py` only sets a flash message and redirects without regenerating the PDF document.

### 3.14 PDF Download Functionality
- Powered by ReportLab in `reports/views.py:download_report`.
- Generates a styled A4 document with header, patient metadata, analysis timestamp, model classification badge, confidence probability, processing latency, and medical disclaimers.
- Access is restricted to the owning patient or authenticated administrators.

### 3.15 Chatbot & Medical Knowledge Base
- Server-side integration in `chatbot/services.py` supporting OpenAI (`gpt-4o-mini`), Google Gemini (`gemini-1.5-flash`), and Anthropic Claude (`claude-3-haiku`).
- **Emergency Keyword Detection**: Regex pattern matching for cardiac emergencies ("chest pain", "shortness of breath", "collapsed", "heart attack") returns immediate emergency instructions (911/999/112).
- **Rule-Based Fallback**: When API keys are blank (the default state in `.env`), cleanly serves educational FAQs regarding normal/abnormal heart sounds, MFCC features, and how to upload audio.

### 3.16 Deployment Configuration & Environment Variables
- `.env` contains environment variables for Django secrets, debug flags, AI API keys, and rate limits.
- Render deployment compatibility configured in `settings.py` (`RENDER_EXTERNAL_HOSTNAME`, WhiteNoise static compression, and `gunicorn` in `requirements.txt`).
- Waitress included for Windows production serving.

### 3.17 Error Handling, Security & Testing
- Custom error templates: `templates/errors/403.html`, `404.html`, and `500.html`.
- `AuditLogMiddleware` automatically captures unauthorized 403 access attempts with IP address and user agent.
- Automated test suite in `tests/test_all.py` (319 lines) testing auth, user isolation, audio preprocessing, corrupted file rejection, assessment risk scoring, emergency detection, and admin permissions.

---

## 4. Module-by-Module Audit Summary

| Module / Application | Primary Responsible Files | Working Status | Bugs / Incomplete Features | Recommended Improvements |
| :--- | :--- | :---: | :--- | :--- |
| **Accounts** | `accounts/views.py`, `accounts/models.py`, `accounts/forms.py` | **Working** | User deletion request does not purge media files directly. | Add cascading cleanup for avatar and audio files on account removal. |
| **Admin Portal** | `admin_portal/views.py`, `admin_portal/decorators.py` | **Working** | `model_run_eval_view` and `report_regenerate_view` are mock stubs. | Connect real execution of `evaluation.py` and actual PDF regeneration. |
| **Heart Analysis** | `heart_analysis/services.py`, `heart_analysis/views.py` | **Working** | Audio processing runs synchronously in HTTP request loop; deleting recording leaves plot images in `media/analysis_plots/`. | Add timeout guards / async execution; delete plot files on `AnalysisRecord.delete()`. |
| **ML Pipeline** | `ml_pipeline/prediction.py`, `ml_pipeline/audio_processing.py` | **Working** | Model trained on only 30 synthetic samples; `ModelMetadata` DB table is unpopulated. | Populate DB model tracking table; provide real PhysioNet dataset training pipeline. |
| **Assessments** | `assessments/models.py`, `assessments/views.py` | **Working** | None. Rule-based risk computation works reliably. | Add option to export assessment history as CSV or include in PDF. |
| **Chatbot** | `chatbot/services.py`, `chatbot/views.py` | **Working** | Live LLMs require API keys in `.env`; fallback FAQ active. | Provide clearer UI badge indicating when running in rule-based vs live AI mode. |
| **Reports** | `reports/views.py` | **Working** | Only PDF export available; no user-facing CSV history export. | Add user-facing CSV export for personal history. |
| **Core & Backups** | `core/management/commands/backup_data.py`, `core/models.py` | **Partial** | `backup_data.py` backs up SQLite database but omits user media files. | Update `backup_data.py` to archive the `media/` directory alongside `db.sqlite3`. |
| **Dashboard** | `dashboard/views.py`, `dashboard/templates/` | **Working** | Chart.js 14-day history relies on client-side JS without date filtering controls. | Add date range filter selector. |
