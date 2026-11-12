# Machine Learning Models Directory

This folder stores the serialized machine learning model files, feature scaler, and execution metadata.

---

## Model Artifacts

1. **`heart_sound_classifier.pkl`**: Serialized `RandomForestClassifier` trained on normalized, resampled audio features.
2. **`scaler.pkl`**: `StandardScaler` fitted on the training split feature matrix to ensure zero-mean, unit-variance normalization during inference.
3. **`model_metadata.json`**: Auditable model training metadata (version, hyperparameters, cross-validation metrics, confusion matrix, sensitivity, specificity).

---

## Model Generation

Run the end-to-end training pipeline:

```powershell
python ml_pipeline/model_training.py --dataset_dir datasets/ --output_dir ml_models/
```

If these files are missing or deleted, the web application enters a safe `model_unavailable` state without throwing uncaught exceptions or presenting fabricated classification predictions.
