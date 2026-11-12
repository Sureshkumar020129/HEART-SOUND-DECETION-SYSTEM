"""
prediction.py
-------------
Loads the trained ML model and scaler, runs inference on a feature vector,
and returns a structured result dict.

Design principles:
  - Never returns a fabricated result.
  - If the model file is missing, returns model_unavailable status clearly.
  - Confidence score is the model's output probability, NOT a clinical probability.
  - All results are clearly labelled as research-only screening output.
"""

import os
import logging
import pickle
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

DISCLAIMER = (
    "This classification was produced by a machine-learning model for research "
    "and educational screening support only. It is NOT a clinical diagnosis and "
    "must NOT be used as a substitute for professional medical evaluation."
)


class ModelNotAvailableError(Exception):
    """Raised when the saved model files cannot be found or loaded."""
    pass


class PredictionError(Exception):
    """Raised when model inference fails."""
    pass


def load_model(model_path: str, scaler_path: str):
    """
    Load the classifier and scaler from disk.

    Raises ModelNotAvailableError if either file is missing or corrupt.
    """
    model_path = Path(model_path)
    scaler_path = Path(scaler_path)

    if not model_path.exists():
        raise ModelNotAvailableError(
            f"Model file not found at: {model_path}. "
            "Please train and save the model first. "
            "See ml_pipeline/model_training.py and datasets/README.md."
        )
    if not scaler_path.exists():
        raise ModelNotAvailableError(
            f"Scaler file not found at: {scaler_path}. "
            "Please run training to generate the scaler."
        )

    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        logger.info(f"Model loaded from {model_path}")
        return model, scaler
    except Exception as exc:
        raise ModelNotAvailableError(f"Failed to deserialize model: {exc}")


def predict(features: np.ndarray, model_path: str, scaler_path: str, model_version: str = '1.0.0') -> dict:
    """
    Run inference on a feature vector.

    Args:
        features: 1D np.ndarray from feature_extraction.extract_all_features()
        model_path: path to the pickled classifier
        scaler_path: path to the pickled scaler
        model_version: version string for audit

    Returns a dict:
        {
            'status': 'success' | 'model_unavailable' | 'error',
            'classification': 'normal' | 'abnormal' | 'uncertain' | 'model_unavailable',
            'confidence_score': float | None,
            'raw_scores': dict | None,
            'model_name': str,
            'model_version': str,
            'disclaimer': str,
            'error_message': str (only on failure),
        }
    """
    result_base = {
        'model_name': 'HeartSoundClassifier',
        'model_version': model_version,
        'disclaimer': DISCLAIMER,
    }

    # --- Load model ---
    try:
        model, scaler = load_model(model_path, scaler_path)
    except ModelNotAvailableError as exc:
        logger.warning(f"Model unavailable: {exc}")
        return {
            **result_base,
            'status': 'model_unavailable',
            'classification': 'model_unavailable',
            'confidence_score': None,
            'raw_scores': None,
            'error_message': str(exc),
        }

    # --- Validate feature shape ---
    if features is None or len(features) == 0:
        return {
            **result_base,
            'status': 'error',
            'classification': 'uncertain',
            'confidence_score': None,
            'raw_scores': None,
            'error_message': 'Feature vector is empty.',
        }

    # --- Scale features ---
    try:
        features_2d = features.reshape(1, -1)
        features_scaled = scaler.transform(features_2d)
    except Exception as exc:
        logger.error(f"Scaler transform failed: {exc}")
        return {
            **result_base,
            'status': 'error',
            'classification': 'uncertain',
            'confidence_score': None,
            'raw_scores': None,
            'error_message': (
                f"Feature shape mismatch with trained scaler: {exc}. "
                "Ensure the model and scaler were trained on the same feature set."
            ),
        }

    # --- Run inference ---
    try:
        pred_class = model.predict(features_scaled)[0]
        # Map class labels (the training script uses 0=normal, 1=abnormal)
        label_map = {0: 'normal', 1: 'abnormal', 'normal': 'normal', 'abnormal': 'abnormal'}
        classification = label_map.get(pred_class, str(pred_class))

        confidence_score = None
        raw_scores = None
        if hasattr(model, 'predict_proba'):
            proba = model.predict_proba(features_scaled)[0]
            classes = model.classes_
            raw_scores = {label_map.get(c, str(c)): float(p) for c, p in zip(classes, proba)}
            confidence_score = float(np.max(proba))

        logger.info(f"Prediction: {classification}, confidence: {confidence_score}")
        return {
            **result_base,
            'status': 'success',
            'classification': classification,
            'confidence_score': confidence_score,
            'raw_scores': raw_scores,
            'error_message': '',
        }

    except Exception as exc:
        logger.error(f"Inference failed: {exc}")
        return {
            **result_base,
            'status': 'error',
            'classification': 'uncertain',
            'confidence_score': None,
            'raw_scores': None,
            'error_message': f"Model inference error: {exc}",
        }
