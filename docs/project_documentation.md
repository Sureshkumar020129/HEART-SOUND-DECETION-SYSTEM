# Complete Project Documentation & Technical Report
## AI-Powered Heart Sound Disease Detection System

---

## 1. Project Abstract

Cardiovascular diseases remain the leading contributor to non-communicable global mortality. While mechanical auscultation via stethoscope is the first clinical line of defense, accurate acoustic perception of subtle murmurs, extra heart sounds (S3, S4), and valve regurgitation depends heavily on practitioner experience and ambient noise levels. 

The **AI-Powered Heart Sound Disease Detection System** is an end-to-end full-stack web application developed with Python, Django, Librosa, Scikit-learn, and ReportLab. It provides automated, reproducible preprocessing, acoustic feature extraction (MFCCs, spectral contrast, chroma, and mel filterbank energies), and classification into *Normal* and *Abnormal* heart sounds. The system features a modern animated dashboard, real database tracking, browser-based microphone recording, downloadable clinical PDF screening reports, a validated health questionnaire, and a conversational AI healthcare assistant equipped with emergency symptom detection.

---

## 2. Problem Statement

1. **Auscultation Subjectivity:** Conventional stethoscopes lack objective recordability, frequency filtering, and reproducible visual confirmation.
2. **Access Inequity:** Access to skilled cardiologists and Doppler echocardiography equipment in rural or underserved clinics is severely constrained.
3. **Black-box AI Proliferation:** Many online health demos use hardcoded scripts, fake random numbers, or opaque models that confuse algorithmic confidence with actual diagnostic disease probability.
4. **Lack of Emergency Triage:** Generic chatbots frequently offer routine conversational advice when users present acute emergency symptoms (such as crushing chest pain or syncope), creating severe liability and patient risk.

---

## 3. Project Objectives

- **Develop a Secure Full-Stack Web Platform:** Django backend with SQLite, CSRF tokens, hashed credential storage, and cross-user data isolation.
- **Implement a Real Acoustic Signal Processing Engine:** Support WAV, FLAC, MP3, and OGG formats with resampling to 22,050 Hz, mono conversion, time alignment, and peak normalization.
- **Extract Multi-Domain Audio Features:** Compute a 190-dimensional feature vector combining 40-order MFCC statistics, chroma vectors, spectral contrast, spectral moments, and zero-crossing rates.
- **Deploy an Auditable Machine Learning Classifier:** Train and evaluate an ensemble classifier on benchmark phonocardiogram data without data leakage.
- **Provide Medical Screening Documentation:** Generate formal ReportLab PDF reports incorporating waveform plots, spectrograms, model version numbers, and disclaimers.
- **Integrate an AI Healthcare Chatbot:** Provide a responsive assistant with dual-mode LLM API integration and an internal rule-based emergency triage fallback.

---

## 4. Existing System vs. Proposed System

| Dimension | Existing / Traditional Approach | Proposed HeartSound AI System |
|---|---|---|
| **Audio Capture** | Acoustic binaural stethoscope, ephemeral listening | Digital upload + Web Audio API browser recording + Persistent isolated storage |
| **Analysis Method** | Qualitative subjective human listening | Quantitative 190-dimensional feature extraction + ML classification |
| **Visual Verification** | None | Real-time generated time-domain waveform and Mel-spectrogram images |
| **Transparency** | Binary diagnosis without confidence context | Explicit model probability separated from clinical disease likelihood |
| **User Access** | In-clinic visits only | Responsive web application with user dashboard and history tracking |
| **Safety & Triage** | Dependent on clinical staff availability | Built-in symptom assessment tool and AI emergency triage interceptor |

---

## 5. Technology Stack & Packages

- **Web Framework:** Django 6.1 (Python 3.14)
- **Frontend Architecture:** HTML5, CSS3 Keyframe Animations, Bootstrap 5.3, Bootstrap Icons, AOS (Animate on Scroll)
- **Data Visualizations:** Chart.js (Dashboard activity & classification breakdown)
- **Audio Processing:** Librosa 1.0, SoundFile 0.14, NumPy 2.5, SciPy 1.18
- **Plotting & Visualization:** Matplotlib 3.11 (Headless Agg backend)
- **Machine Learning Engine:** Scikit-Learn 1.9 (RandomForestClassifier, StandardScaler, StratifiedKFold, ROC-AUC metrics)
- **PDF Report Generation:** ReportLab 5.1
- **Static Asset Delivery:** WhiteNoise 6.12
- **Environment Management:** python-dotenv 1.2

---

## 6. Functional & Non-Functional Requirements

### Functional Requirements
- **FR-1:** User registration with explicit informed data consent checkbox.
- **FR-2:** Multi-format audio upload and client-side browser microphone recording.
- **FR-3:** Audio signal validation rejecting silent or corrupted recordings.
- **FR-4:** Automated feature extraction (MFCCs, Chroma, Contrast, Spectral Shape, ZCR, Mel energies).
- **FR-5:** ML prediction with confidence probability, handling missing models gracefully.
- **FR-6:** Downloadable PDF clinical report generation.
- **FR-7:** 14-question symptom assessment scoring into Low, Moderate, High, and Seek Urgent Care.
- **FR-8:** AI Healthcare chatbot with emergency detection and FAQ fallback mode.
- **FR-9:** User deletion rights for private audio files and analysis records.

### Non-Functional Requirements
- **NFR-1 (Security):** All passwords hashed via PBKDF2; CSRF protection on all mutating POST requests.
- **NFR-2 (Privacy):** Audio files stored with random UUID identifiers in user-isolated paths.
- **NFR-3 (Performance):** Average preprocessing and prediction inference under 1,500 ms.
- **NFR-4 (Accessibility):** Dark medical UI with WCAG AA compliant contrast ratios and `prefers-reduced-motion` support.
- **NFR-5 (Reliability):** Absence of model files triggers safe `model_unavailable` states rather than 500 runtime crashes.

---

## 7. Machine Learning Pipeline Specification

```text
Audio File (.wav, .flac)
       │
       ▼
[audio_processing.py]
  - sf.info() validation (Duration: 1.0s to 300.0s)
  - Stereo downmixed to Mono
  - Librosa Resampling to 22,050 Hz
  - Peak Amplitude Normalization (Audio / max(|Audio|))
  - Pad / Trim to fixed 5.0-second window
       │
       ▼
[feature_extraction.py]
  - MFCCs: 40 coefficients x (Mean + Std) = 80 features
  - Chroma STFT: 12 bins x (Mean + Std)    = 24 features
  - Spectral Contrast: 7 bands x (Mean + Std) = 14 features
  - Spectral Centroid & Bandwidth           = 4 features
  - Zero-Crossing Rate & RMS Energy          = 4 features
  - Mel-Filterbank Energies (64 bands)      = 64 features
  Total Vector Length = 190 numerical features
       │
       ▼
[prediction.py]
  - Transform via fitted StandardScaler (ml_models/scaler.pkl)
  - Evaluate with RandomForestClassifier (ml_models/heart_sound_classifier.pkl)
  - Compute softmax predict_proba distribution
  - Return: classification ('normal' / 'abnormal') + confidence + raw score map
```

---

## 8. Chatbot Safety Architecture

The **HeartCare AI Assistant** runs exclusively on the server side:
1. **Regex Emergency Filter:** Inspects input for symptoms including severe chest pain, inability to breathe, heart attack indicators, or collapse.
2. **Immediate Override:** If detected, halts conversational routines and outputs prominent red emergency instructions to call local emergency dispatchers immediately.
3. **Provider Selection:** Connects to OpenAI, Gemini, or Claude if API keys exist in `.env`.
4. **Fallback Knowledgebase:** If keys are unset, delivers curated responses regarding heart sound physics, murmur definitions, and report navigation.

---

## 9. Known Limitations & Future Scope

- **Acoustic Noise Sensitivity:** Heavy ambient friction or talking during recording degrades classifier accuracy.
- **Binary Classification Scope:** Current model distinguishes between Normal and Abnormal; future iterations can classify specific murmurs (Aortic Regurgitation, Mitral Stenosis, Tricuspid Murmurs).
- **Embedded Edge Deployment:** Future enhancements include WebAssembly / ONNX client-side inference on mobile devices for offline community health worker deployment.
