# HeartSound AI — Feature Recommendations & Prioritization (PHASES 2 & 3)

**Project Name:** AI-Powered Heart Sound Disease Detection System  
**Document:** Feature Classification, Architecture Recommendations & Prioritization  
**Target Architecture:** Django 6.1, SQLite 3, Scikit-learn, Librosa, ReportLab, Bootstrap 5.3  

---

## 1. Feature Classification

### CATEGORY A &mdash; MUST ADD (Essential Missing / Incomplete Features)
These items address direct operational shortcomings, potential data loss, incomplete administrative endpoints, and security/maintenance issues identified during the audit:

1. **Media Archive & Automated Backup Extension:**  
   Extend `core/management/commands/backup_data.py` to create timestamped archive snapshots of the `media/` directory (`heart_sounds/` and `analysis_plots/`) alongside `db.sqlite3`.
2. **Orphaned Media Cleanup on Record Deletion:**  
   Ensure that deleting an `AnalysisRecord` or `HeartSoundRecording` purges the generated waveform and spectrogram PNG files from `media/analysis_plots/` in addition to the raw audio file.
3. **User-Facing Personal History CSV Export:**  
   Standard patients can download PDF reports, but have no way to export their historical analysis screenings or symptom questionnaires to CSV.
4. **Live Administrative Model Evaluation Pipeline:**  
   Replace the flash-message stub in `admin_portal/views.py:model_run_eval_view` with actual execution of `ml_pipeline/evaluation.py` against the benchmark dataset, outputting live metrics and confusion matrices.
5. **Populate `ModelMetadata` Database Model:**  
   Write model performance metrics, dataset version, and parameter configurations directly into the `ModelMetadata` table on training/evaluation, replacing reliance on static JSON parsing.
6. **Report Regeneration Logic:**  
   Implement real PDF cache purging and document regeneration in `admin_portal/views.py:report_regenerate_view`.
7. **Environment & Security Hardening:**  
   Generate and configure a strong cryptographically secure Django `SECRET_KEY` in `.env` to replace placeholder defaults.

---

### CATEGORY B &mdash; RECOMMENDED (Enhancements to User Experience & Usability)
These improvements enhance workflow efficiency, visual transparency, and diagnostic comprehension:

1. **Audio Playback Preview Before Analysis:**  
   Allow users to play back their uploaded or browser-recorded audio file with a lightweight HTML5/Web Audio waveform preview before submitting it for ML inference.
2. **Analysis Upload Progress Indicator:**  
   Provide a multi-stage visual progress indicator ("Uploading &rarr; Preprocessing Audio &rarr; Extracting Features &rarr; ML Inference &rarr; Complete") to improve perceived responsiveness during 2–3 second Librosa processing cycles.
3. **Search & Filter Controls for Personal History:**  
   Provide date-range selectors, classification filters (`Normal`, `Abnormal`, `Uncertain`), and keyword search in `/analysis/history/` and `/assessment/history/`.
4. **Educational Heart Sound Library:**  
   Provide a curated educational page featuring reference phonocardiogram audio samples (Normal S1/S2 Lub-Dub vs Systolic Murmurs) so patients can understand what the AI model evaluates.
5. **Doctor / Clinician Review & Notes Model:**  
   Introduce an optional `DoctorReview` or `ClinicalNote` relationship enabling an authenticated medical administrator or clinician to add observational notes to an analysis.
6. **Detailed Acoustic Feature Explanation on Result Page:**  
   Add an expandable panel explaining what MFCCs, Spectral Centroid, and Chroma mean in layperson terms, helping users understand why the sound was classified as Normal or Abnormal.

---

### CATEGORY C &mdash; ADVANCED (Professional Healthcare Technology Capabilities)
High-value capabilities for extended research and enterprise scaling:

1. **Interactive Phonocardiogram (PCG) Waveform Scrubbing Player:**  
   An interactive Canvas or Wavesurfer-based player that synchronizes audio playback with a moving cursor along the heart sound waveform.
2. **Model Latency & Prediction Distribution Drift Monitoring:**  
   Real-time administrative analytics tracking the rolling 30-day ratio of Normal vs Abnormal predictions to detect potential model or sensor drift.
3. **Multi-Model Benchmark & Comparison:**  
   Allow administrators to evaluate multiple classifiers (e.g. `RandomForestClassifier` vs `GradientBoostingClassifier` vs `SVM`) on the evaluation dataset side-by-side.
4. **PhysioNet / CinC Challenge 2016 Real-Dataset Retraining Pipeline:**  
   An automated script to download and train on the open-access PhysioNet Challenge 2016 clinical phonocardiogram dataset, replacing the synthetic 30-sample starter model.
5. **Explainable AI (Feature Importance Attribution):**  
   Extract and visualize top Random Forest Gini feature importances for each classification.

---

## 2. Feature Prioritization Matrix

| Feature | Existing Status | Priority | Difficulty | Recommendation |
| :--- | :---: | :---: | :---: | :--- |
| **Media File Backup in `backup_data.py`** | Missing | **Critical** | Low | Archive `media/` directory into zip/tar along with `db.sqlite3` during backup runs. |
| **Orphaned Media Cleanup on Deletion** | Missing | **Critical** | Low | Connect Django `post_delete` signals on `AnalysisRecord` to purge PNG plot files from disk. |
| **Secure `SECRET_KEY` Generation** | Partial | **Critical** | Low | Replace `.env` placeholder with a secure 50-character random key. |
| **User Personal History CSV Export** | Missing | **High** | Low | Add `/analysis/history/export/csv/` and `/assessment/history/export/csv/` for users. |
| **Live Admin Model Evaluation** | Partial (Stub) | **High** | Medium | Connect `model_run_eval_view` to execute `evaluation.py` and display live benchmark results. |
| **Populate `ModelMetadata` DB Table** | Missing | **High** | Low | Write evaluation output into `heart_analysis.models.ModelMetadata`. |
| **Audio Playback Preview Before Submit** | Missing | **High** | Medium | Add audio element and waveform visualizer to `heart_analysis/upload.html`. |
| **Analysis Progress Bar / Loading State** | Partial | **High** | Low | Enhance JavaScript form submission handler with an active multi-step loading spinner. |
| **Search & Filters in User History** | Missing | **Medium** | Low | Add search form and query filtering to `heart_analysis/views.py:history_view`. |
| **Doctor Review / Clinical Feedback Note**| Missing | **Medium** | Medium | Add `DoctorReview` model to allow medical admins to append notes to an analysis. |
| **Educational Heart Sound Library** | Missing | **Medium** | Low | Create a reference audio sample player page under `core` explaining cardiac acoustic landmarks. |
| **Interactive PCG Waveform Player** | Partial (Static PNG) | **Medium** | Medium | Enhance result view with interactive audio playback synced to waveform visualization. |
| **PhysioNet Clinical Dataset Ingestion** | Script exists | **Optional** | High | Integrate automated downloading of PhysioNet 2016 for production-grade retraining. |
| **Model Drift & Latency Tracking** | Partial (Avg latency) | **Optional** | Medium | Add rolling classification distribution chart in the Admin Portal. |

---

## 3. Dependencies and Risk Assessment

| Feature | Dependencies | Identified Risks | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Media Backup Extension** | Python `shutil`, `zipfile`, disk space | Large media directories can slow backup execution or consume high disk storage. | Back up only referenced media files; implement configurable retention pruning for backups. |
| **Orphaned File Deletion** | Django `post_delete` signal, OS file removal | Race condition if file is missing from disk during deletion attempt. | Wrap disk unlinking in `try/except FileNotFoundError` blocks. |
| **Live Model Evaluation** | Scikit-learn, NumPy, Librosa, dataset files | Running evaluation synchronously on large datasets could trigger HTTP worker timeouts. | Evaluate against the precomputed test split or guard with an execution timer. |
| **Doctor Review Feature** | Django ORM migration, user permissions | Database migration required; must not alter existing `AnalysisRecord` foreign keys. | Add nullable foreign key or `OneToOneField(null=True)` with backward-compatible migrations. |
| **User History CSV Export** | Python standard `csv` module | Potential leakage of sensitive records if user isolation is violated. | Strictly enforce `AnalysisRecord.objects.filter(user=request.user)`. |

---

## 4. Medical and Legal Safety Compliance Rules

1. **Screening Support Only:** The web application and AI assistant must clearly and repeatedly communicate that predictions are experimental decision-support outputs, not clinical diagnoses.
2. **Definitive Diagnosis Prohibition:** The system must never claim definitive diagnostic certainty (e.g. stating "You have heart disease"). Output must remain probabilistic (e.g. "Acoustic pattern classified as Abnormal; clinical auscultation recommended").
3. **No Medication or Treatment Prescriptions:** The chatbot and reports must never suggest specific drugs, dosages, or self-treatments.
4. **Emergency Protocols:** In-app emergency detection must remain functional at all times, directing acute patients immediately to emergency contact numbers (911, 999, 112).
5. **No Fabricated Performance:** Model metrics must always be reported as observed on verified test datasets; synthetic training limitations must be transparently disclosed.
