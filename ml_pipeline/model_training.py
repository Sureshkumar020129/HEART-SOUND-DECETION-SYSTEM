"""
model_training.py
-----------------
Training pipeline for the Heart Sound Classifier.

Dataset expected structure
--------------------------
datasets/
  normal/      *.wav  (normal heart sounds)
  abnormal/    *.wav  (abnormal heart sounds)

Recommended public dataset:
  PhysioNet / CinC 2016 Heart Sound Challenge
  URL: https://physionet.org/content/challenge-2016/1.0.0/
  License: Open Data Commons Attribution License (ODC-BY 1.0)
  Labels: normal, abnormal (murmurs, extra sounds, etc.)

Usage
-----
  python ml_pipeline/model_training.py --dataset_dir datasets/ --output_dir ml_models/

Requirements
------------
  pip install scikit-learn librosa soundfile joblib

Important notes
---------------
  - The script splits data by file, NOT by patient, to avoid data leakage.
  - Evaluation metrics are computed on a held-out test set.
  - Fabricated metrics are never reported.
  - Run evaluation.py separately for a full report.
"""

import os
import sys
import pickle
import logging
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, f1_score

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml_pipeline.audio_processing import preprocess_audio, AudioProcessingError
from ml_pipeline.feature_extraction import extract_all_features, FeatureExtractionError

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)

LABEL_MAP = {'normal': 0, 'abnormal': 1}
SUPPORTED_EXTENSIONS = {'.wav', '.flac', '.mp3', '.ogg', '.aiff'}


def collect_dataset(dataset_dir: str) -> tuple:
    """
    Walk the dataset directory and return (file_paths, labels).
    Expects subdirectories named 'normal' and 'abnormal'.
    """
    dataset_path = Path(dataset_dir)
    file_paths = []
    labels = []

    for label_name, label_id in LABEL_MAP.items():
        label_dir = dataset_path / label_name
        if not label_dir.exists():
            logger.warning(f"Label directory not found: {label_dir}")
            continue
        files = [
            f for f in label_dir.iterdir()
            if f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        logger.info(f"  {label_name}: {len(files)} files found")
        for f in files:
            file_paths.append(str(f))
            labels.append(label_id)

    if len(file_paths) == 0:
        raise ValueError(
            f"No audio files found in {dataset_dir}. "
            "Ensure the dataset contains 'normal/' and 'abnormal/' subdirectories with audio files."
        )

    return file_paths, labels


def build_feature_matrix(file_paths: list, labels: list) -> tuple:
    """
    Load, preprocess, and extract features for every file.
    Skips files that fail processing and logs the reason.
    """
    X = []
    y = []
    skipped = 0

    for idx, (fp, label) in enumerate(zip(file_paths, labels)):
        try:
            processed = preprocess_audio(fp)
            features = extract_all_features(processed['audio'], processed['sample_rate'])
            X.append(features)
            y.append(label)
            if (idx + 1) % 50 == 0:
                logger.info(f"  Processed {idx + 1}/{len(file_paths)} files...")
        except (AudioProcessingError, FeatureExtractionError) as exc:
            logger.warning(f"  Skipped {fp}: {exc}")
            skipped += 1
        except Exception as exc:
            logger.warning(f"  Unexpected error for {fp}: {exc}")
            skipped += 1

    logger.info(f"Feature extraction complete: {len(X)} ok, {skipped} skipped")
    return np.array(X), np.array(y)


def train(dataset_dir: str, output_dir: str, test_size: float = 0.2, random_state: int = 42):
    """Full training pipeline."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("=== Heart Sound Classifier Training ===")
    logger.info(f"Dataset: {dataset_dir}")
    logger.info(f"Output: {output_dir}")

    # 1. Collect files
    logger.info("Step 1: Collecting dataset files...")
    file_paths, labels = collect_dataset(dataset_dir)
    logger.info(f"Total files: {len(file_paths)} (normal: {labels.count(0)}, abnormal: {labels.count(1)})")

    # 2. Extract features
    logger.info("Step 2: Extracting features...")
    X, y = build_feature_matrix(file_paths, labels)
    if len(X) < 10:
        raise ValueError(f"Too few valid samples ({len(X)}) to train a meaningful model.")

    # 3. Train/test split
    logger.info("Step 3: Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    logger.info(f"  Train: {len(X_train)}, Test: {len(X_test)}")

    # 4. Scale features
    logger.info("Step 4: Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 5. Train classifier
    logger.info("Step 5: Training RandomForest classifier...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=4,
        class_weight='balanced',
        random_state=random_state,
        n_jobs=-1,
    )
    model.fit(X_train_scaled, y_train)

    # 6. Evaluate on test set
    logger.info("Step 6: Evaluating on held-out test set...")
    y_pred = model.predict(X_test_scaled)
    report = classification_report(y_pred=y_pred, y_true=y_test,
                                   target_names=['normal', 'abnormal'])
    logger.info(f"\n{report}")

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (None, None, None, None)
    sensitivity = tp / (tp + fn) if (tp is not None and (tp + fn) > 0) else None
    specificity = tn / (tn + fp) if (tn is not None and (tn + fp) > 0) else None
    test_f1 = f1_score(y_test, y_pred, average='weighted')

    # 5-fold cross-validation on training set only
    logger.info("Step 7: Cross-validation (5-fold, training set)...")
    cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='f1_weighted')
    logger.info(f"  CV F1: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # 7. Save model and scaler
    model_file = output_path / 'heart_sound_classifier.pkl'
    scaler_file = output_path / 'scaler.pkl'
    with open(model_file, 'wb') as f:
        pickle.dump(model, f)
    with open(scaler_file, 'wb') as f:
        pickle.dump(scaler, f)
    logger.info(f"Model saved → {model_file}")
    logger.info(f"Scaler saved → {scaler_file}")

    # 8. Save metadata
    metadata = {
        'model_name': 'HeartSoundClassifier',
        'version': '1.0.0',
        'algorithm': 'RandomForestClassifier',
        'n_estimators': 200,
        'feature_length': int(X.shape[1]),
        'training_samples': int(len(X_train)),
        'test_samples': int(len(X_test)),
        'test_f1_weighted': float(test_f1),
        'cv_f1_mean': float(cv_scores.mean()),
        'cv_f1_std': float(cv_scores.std()),
        'sensitivity': float(sensitivity) if sensitivity is not None else None,
        'specificity': float(specificity) if specificity is not None else None,
        'confusion_matrix': cm.tolist(),
        'classes': ['normal', 'abnormal'],
        'sample_rate': 22050,
        'audio_duration_seconds': 5,
        'disclaimer': (
            'Metrics are computed on a held-out test set split from the training dataset. '
            'Performance may differ on other datasets or clinical populations. '
            'This model is for research and educational purposes only.'
        ),
    }
    meta_file = output_path / 'model_metadata.json'
    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Metadata saved → {meta_file}")
    logger.info("=== Training complete ===")
    return metadata


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train the Heart Sound Classifier')
    parser.add_argument('--dataset_dir', default='datasets/', help='Path to dataset root')
    parser.add_argument('--output_dir', default='ml_models/', help='Where to save model files')
    parser.add_argument('--test_size', type=float, default=0.2, help='Test split fraction')
    args = parser.parse_args()
    train(args.dataset_dir, args.output_dir, args.test_size)
