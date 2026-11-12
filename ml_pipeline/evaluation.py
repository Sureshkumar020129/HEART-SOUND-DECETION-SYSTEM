"""
evaluation.py
-------------
Standalone evaluation script for a trained heart sound classifier.

Usage:
  python ml_pipeline/evaluation.py --model_dir ml_models/ --dataset_dir datasets/

Outputs:
  - Detailed classification report
  - Confusion matrix
  - Sensitivity / Specificity
  - ROC-AUC (if supported)
"""

import sys
import pickle
import logging
import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_score, recall_score, f1_score, accuracy_score
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml_pipeline.model_training import collect_dataset, build_feature_matrix

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
logger = logging.getLogger(__name__)


def evaluate(model_dir: str, dataset_dir: str):
    model_path = Path(model_dir) / 'heart_sound_classifier.pkl'
    scaler_path = Path(model_dir) / 'scaler.pkl'

    if not model_path.exists() or not scaler_path.exists():
        logger.error(f"Model files not found in {model_dir}. Train the model first.")
        return

    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)

    logger.info("Loading evaluation dataset...")
    file_paths, labels = collect_dataset(dataset_dir)
    X, y = build_feature_matrix(file_paths, labels)

    X_scaled = scaler.transform(X)
    y_pred = model.predict(X_scaled)

    logger.info("\n=== Evaluation Report ===")
    logger.info(classification_report(y, y_pred, target_names=['normal', 'abnormal']))

    cm = confusion_matrix(y, y_pred)
    logger.info(f"Confusion Matrix:\n{cm}")

    if cm.shape == (2, 2):
        tn, fp, fn, tp = cm.ravel()
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        logger.info(f"Sensitivity (Recall for 'abnormal'): {sensitivity:.4f}")
        logger.info(f"Specificity (Recall for 'normal'):   {specificity:.4f}")

    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(X_scaled)[:, 1]
        try:
            auc = roc_auc_score(y, proba)
            logger.info(f"ROC-AUC: {auc:.4f}")
        except Exception:
            pass

    logger.info(f"Overall Accuracy:  {accuracy_score(y, y_pred):.4f}")
    logger.info(f"Weighted F1-Score: {f1_score(y, y_pred, average='weighted'):.4f}")
    logger.info("=== End of Report ===")
    logger.info("\nIMPORTANT: These metrics are for research evaluation only.")
    logger.info("Clinical validation requires a separate prospective study.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Evaluate the trained heart sound classifier.')
    parser.add_argument('--model_dir', default='ml_models/')
    parser.add_argument('--dataset_dir', default='datasets/')
    args = parser.parse_args()
    evaluate(args.model_dir, args.dataset_dir)
