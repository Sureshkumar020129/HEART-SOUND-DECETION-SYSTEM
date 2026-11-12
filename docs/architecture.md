# System Architecture & Technical Specification

## 1. High-Level Architectural Overview

The **AI-Powered Heart Sound Disease Detection System** is structured as an enterprise-grade multi-tier Django web application coupled with a modular audio signal processing and machine learning inference engine.

```mermaid
graph TD
    User([End User / Clinician]) <-->|HTTPS / Web Interface| WebLayer[Nginx / WhiteNoise & Django HTTP Layer]
    
    subgraph WebLayer [Django Application Layer]
        AuthMod[Module 1: Authentication & RBAC]
        DashMod[Module 2: Dashboard Engine]
        AudioIngest[Module 3: Audio Ingestion & Web Recording]
        AssessMod[Module 7: Heart Health Assessment]
        ChatbotMod[Module 8: HeartCare AI Assistant]
        ReportMod[Module 6: PDF Report Generator]
        AuditMod[Module 11: Audit & Rate Limiter]
    end

    subgraph MLPipeline [Module 4 & 5: Acoustic ML Pipeline]
        AudioProc[audio_processing.py: Validation & Normalization]
        FeatExtract[feature_extraction.py: 190-dim MFCC/Spectral Vector]
        InferenceEngine[prediction.py: StandardScaler + RandomForestClassifier]
        ModelStorage[(ml_models: Serialized PKL & Metadata)]
    end

    subgraph DataTier [Module 10: Persistent Data Tier]
        SQLiteDB[(db.sqlite3: Relational ORM Models)]
        MediaStorage[media/heart_sounds: Isolated UUID Encrypted Storage]
    end

    subgraph ExternalServices [External Integrations]
        LLMProviders[OpenAI / Gemini / Anthropic API]
        EmergencyDispatch[Local Urgent Care Guidance]
    end

    AudioIngest --> AudioProc
    AudioProc --> FeatExtract
    FeatExtract --> InferenceEngine
    InferenceEngine <--> ModelStorage
    
    WebLayer <--> SQLiteDB
    AudioIngest --> MediaStorage
    ChatbotMod <--> LLMProviders
    ChatbotMod --> EmergencyDispatch
    ReportMod --> SQLiteDB
```

---

## 2. Ontology Graph

```mermaid
classDiagram
    class User {
        +Integer id
        +String username
        +String email
        +String password_hash
        +Boolean is_staff
    }

    class UserProfile {
        +User user
        +String role
        +Date date_of_birth
        +Boolean data_consent
        +DateTime data_consent_at
    }

    class HeartSoundRecording {
        +UUID id
        +User user
        +File audio_file
        +String source
        +Float duration_seconds
        +Integer sample_rate
        +String status
        +DateTime uploaded_at
    }

    class AnalysisRecord {
        +UUID id
        +User user
        +HeartSoundRecording recording
        +String status
        +Integer processing_duration_ms
        +Image waveform_image
        +Image spectrogram_image
    }

    class PredictionResult {
        +AnalysisRecord analysis
        +String model_name
        +String model_version
        +String classification
        +Float confidence_score
        +JSON raw_scores
        +JSON feature_summary
        +String disclaimer
    }

    class HealthAssessment {
        +User user
        +Integer age
        +String chest_discomfort
        +Integer chest_pain_level
        +String shortness_of_breath
        +String fainting
        +String risk_level
        +DateTime submitted_at
    }

    class ChatSession {
        +UUID id
        +User user
        +Boolean is_active
        +DateTime started_at
    }

    class ChatMessage {
        +ChatSession session
        +String role
        +String content
        +String source
        +DateTime timestamp
    }

    class AuditLog {
        +User user
        +String action
        +String description
        +IPAddress ip_address
        +DateTime timestamp
    }

    User "1" --> "1" UserProfile : owns
    User "1" --> "many" HeartSoundRecording : submits
    User "1" --> "many" AnalysisRecord : initiates
    HeartSoundRecording "1" --> "many" AnalysisRecord : processed_in
    AnalysisRecord "1" --> "1" PredictionResult : yields
    User "1" --> "many" HealthAssessment : completes
    User "1" --> "many" ChatSession : converses
    ChatSession "1" --> "many" ChatMessage : contains
    User "1" --> "many" AuditLog : tracked_in
```

---

## 3. Data Flow Diagrams

### Level 0 DFD (Context Diagram)

```mermaid
flowchart TD
    Patient([Patient / User]) -->|1. Submit Audio Recording or Browser Mic Stream| HeartSoundApp[AI-Powered Heart Sound Disease Detection System]
    Patient -->|2. Submit Questionnaire Symptoms| HeartSoundApp
    Patient -->|3. Chat Prompts & Inquiries| HeartSoundApp
    
    HeartSoundApp -->|A. Formatted PDF Clinical Screening Report| Patient
    HeartSoundApp -->|B. Mel-Spectrogram & Waveform Visuals| Patient
    HeartSoundApp -->|C. Classification & Confidence Metrics| Patient
    HeartSoundApp -->|D. HeartCare AI Educational & Triage Responses| Patient
    
    HeartSoundApp <-->|Query LLM API| CloudLLM([OpenAI / Gemini / Anthropic API])
    HeartSoundApp <-->|Persist Audio & Metadata| Storage[(Disk & SQLite Database)]
```

### Level 1 DFD (Decomposed Module Flow)

```mermaid
flowchart LR
    subgraph S1 [1.0 Ingestion]
        U[User Audio Input] --> Val[Format & Size Validation]
        Val --> StoreAudio[(Encrypted Media Store)]
    end

    subgraph S2 [2.0 Signal Processing]
        StoreAudio --> Resample[Resample 22.05kHz & Mono Downmix]
        Resample --> Norm[Peak Amplitude Normalization]
        Norm --> VisualGen[Matplotlib Waveform & Mel-Spectrogram Generation]
    end

    subgraph S3 [3.0 Feature Extraction]
        Norm --> MFCC[40 MFCC Mean/Std Extraction]
        Norm --> SpecFeat[Spectral Contrast & Chroma]
        Norm --> Energy[ZCR, RMS & Mel Energies]
        MFCC & SpecFeat & Energy --> Concat[190-Dimensional Vector]
    end

    subgraph S4 [4.0 ML Classification]
        Concat --> Scale[StandardScaler Transform]
        Scale --> RF[RandomForest Model Inference]
        RF --> Prob[Softmax / Predict Proba Vector]
    end

    subgraph S5 [5.0 Storage & Reporting]
        Prob --> SavePred[(PredictionResult Model)]
        VisualGen --> SaveVisual[(AnalysisRecord Model)]
        SavePred & SaveVisual --> PDFGen[ReportLab PDF Engine]
        PDFGen --> ClientView[Dashboard & PDF Download]
    end
```
