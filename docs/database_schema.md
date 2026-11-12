# Database Schema & Entity-Relationship Specification

## 1. Relational Database Overview

The application utilizes **SQLite 3** via the **Django Object-Relational Mapper (ORM)**. The schema is organized into normalized relational tables enforcing referential integrity, cascading deletion policies for patient records, and database indexing on frequently queried columns.

```mermaid
erDiagram
    AUTH_USER ||--|| ACCOUNTS_USERPROFILE : "extends"
    AUTH_USER ||--o{ HEARTSOUND_RECORDING : "uploads"
    AUTH_USER ||--o{ HEARTSOUND_ANALYSISRECORD : "owns"
    HEARTSOUND_RECORDING ||--o{ HEARTSOUND_ANALYSISRECORD : "analyzed_by"
    HEARTSOUND_ANALYSISRECORD ||--|| HEARTSOUND_PREDICTIONRESULT : "generates"
    AUTH_USER ||--o{ ASSESSMENTS_HEALTHASSESSMENT : "submits"
    AUTH_USER ||--o{ CHATBOT_CHATSESSION : "initiates"
    CHATBOT_CHATSESSION ||--o{ CHATBOT_CHATMESSAGE : "logs"
    AUTH_USER ||--o{ CORE_AUDITLOG : "audited_in"
    CORE_SITECONFIGURATION

    AUTH_USER {
        int id PK
        string username UK
        string email
        string password
        datetime date_joined
    }

    ACCOUNTS_USERPROFILE {
        int id PK
        int user_id FK
        string role
        string phone
        date date_of_birth
        string avatar
        boolean data_consent
        datetime data_consent_at
    }

    HEARTSOUND_RECORDING {
        uuid id PK
        int user_id FK
        string original_filename
        string audio_file
        string source
        int file_size_bytes
        float duration_seconds
        int sample_rate
        string status
        datetime uploaded_at
    }

    HEARTSOUND_ANALYSISRECORD {
        uuid id PK
        int user_id FK
        uuid recording_id FK
        string status
        int processing_duration_ms
        string waveform_image
        string spectrogram_image
        datetime created_at
    }

    HEARTSOUND_PREDICTIONRESULT {
        int id PK
        uuid analysis_id FK
        string model_name
        string model_version
        string classification
        float confidence_score
        json raw_scores
        json feature_summary
        text disclaimer
        datetime created_at
    }

    ASSESSMENTS_HEALTHASSESSMENT {
        int id PK
        int user_id FK
        int age
        string chest_discomfort
        int chest_pain_level
        string shortness_of_breath
        string shortness_at_rest
        string fainting
        string risk_level
        datetime submitted_at
    }

    CHATBOT_CHATSESSION {
        uuid id PK
        int user_id FK
        boolean is_active
        datetime started_at
        datetime last_active
    }

    CHATBOT_CHATMESSAGE {
        int id PK
        uuid session_id FK
        string role
        text content
        string source
        datetime timestamp
    }

    CORE_AUDITLOG {
        int id PK
        int user_id FK
        string action
        string description
        string ip_address
        datetime timestamp
        boolean success
    }

    CORE_SITECONFIGURATION {
        int id PK
        string site_name
        boolean maintenance_mode
        boolean allow_registration
        boolean chatbot_enabled
        text medical_disclaimer
    }
```

---

## 2. Table Schemas and Constraints

### Table: `accounts_userprofile`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BigAutoField | PRIMARY KEY | Unique ID |
| `user_id` | ForeignKey(`auth_user`) | ON DELETE CASCADE, UNIQUE | Linked Django User |
| `role` | CharField(20) | Choices: `user`, `admin` | User authorization role |
| `phone` | CharField(20) | BLANK=True | User phone contact |
| `date_of_birth` | DateField | NULL=True | Birthday |
| `avatar` | ImageField | Uploads to `avatars/` | Profile picture |
| `data_consent` | BooleanField | DEFAULT=False | Patient research consent flag |
| `data_consent_at` | DateTimeField | NULL=True | Timestamp of legal consent |

### Table: `heart_analysis_heartsoundrecording`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUIDField | PRIMARY KEY, DEFAULT=uuid4 | UUID recording identifier |
| `user_id` | ForeignKey(`auth_user`) | ON DELETE CASCADE | Recording owner |
| `audio_file` | FileField | Validators: WAV, FLAC, MP3, OGG, AIFF | Path to audio on disk |
| `source` | CharField(20) | Choices: `upload`, `browser` | Ingestion method |
| `duration_seconds` | FloatField | NULL=True | Audio duration in seconds |
| `sample_rate` | IntegerField | NULL=True | Ingested audio sample rate |
| `status` | CharField(20) | Choices: `pending`, `processing`, `ready`, `error` | Processing state |
| `uploaded_at` | DateTimeField | AUTO_NOW_ADD=True, INDEX | Ingestion timestamp |

### Table: `heart_analysis_analysisrecord`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUIDField | PRIMARY KEY, DEFAULT=uuid4 | Analysis tracking UUID |
| `user_id` | ForeignKey(`auth_user`) | ON DELETE CASCADE | Associated user |
| `recording_id` | ForeignKey(`heartsoundrecording`) | ON DELETE CASCADE | Associated sound file |
| `status` | CharField(30) | Choices: `queued`, `processing`, `completed`, `failed`, `model_unavailable` | Job status |
| `processing_duration_ms` | IntegerField | NULL=True | Total execution time (ms) |
| `waveform_image` | ImageField | Uploads to `analysis_plots/` | Time-domain plot |
| `spectrogram_image` | ImageField | Uploads to `analysis_plots/` | Frequency-domain mel plot |

### Table: `heart_analysis_predictionresult`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | BigAutoField | PRIMARY KEY | Unique prediction record ID |
| `analysis_id` | OneToOneField(`analysisrecord`) | ON DELETE CASCADE | Linked analysis job |
| `model_name` | CharField(100) | Default: `HeartSoundClassifier` | Model algorithm identifier |
| `model_version` | CharField(50) | Version string | Tracking version |
| `classification` | CharField(30) | Choices: `normal`, `abnormal`, `uncertain`, `model_unavailable` | Category |
| `confidence_score` | FloatField | NULL=True | Probability score (0.0 to 1.0) |
| `raw_scores` | JSONField | NULL=True | Full multi-class probability map |
| `feature_summary` | JSONField | NULL=True | Audit summary of 190-dim features |
| `disclaimer` | TextField | Required | Mandatory legal disclaimer |
