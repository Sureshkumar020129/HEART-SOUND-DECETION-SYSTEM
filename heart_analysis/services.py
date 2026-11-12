"""Heart analysis service: orchestrates audio processing and ML prediction."""
import logging
import time
import base64
import uuid
from io import BytesIO
from pathlib import Path
from django.conf import settings
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


def run_analysis(analysis_record):
    """
    Main entry point: runs the full pipeline for a given AnalysisRecord.
    Updates the record and creates a PredictionResult.
    """
    from heart_analysis.models import PredictionResult
    from ml_pipeline.audio_processing import (
        preprocess_audio, generate_waveform_image, generate_spectrogram_image,
        AudioProcessingError
    )
    from ml_pipeline.feature_extraction import extract_all_features, get_feature_summary, FeatureExtractionError
    from ml_pipeline.prediction import predict

    start_time = time.time()
    recording = analysis_record.recording
    file_path = recording.audio_file.path

    analysis_record.status = 'processing'
    analysis_record.save(update_fields=['status'])

    try:
        # --- Audio Processing ---
        processed = preprocess_audio(file_path)
        audio = processed['audio']
        sr = processed['sample_rate']

        # Update recording metadata
        recording.duration_seconds = processed['duration_seconds']
        recording.sample_rate = processed['original_sr']
        recording.channels = processed['channels']
        recording.status = 'ready'
        recording.save(update_fields=['duration_seconds', 'sample_rate', 'channels', 'status'])

        # --- Generate visualizations ---
        waveform_b64 = generate_waveform_image(audio, sr)
        spectrogram_b64 = generate_spectrogram_image(audio, sr)

        # Save images
        waveform_data = base64.b64decode(waveform_b64)
        spectrogram_data = base64.b64decode(spectrogram_b64)

        waveform_file = ContentFile(waveform_data, name=f"waveform_{analysis_record.id}.png")
        spectrogram_file = ContentFile(spectrogram_data, name=f"spectrogram_{analysis_record.id}.png")
        analysis_record.waveform_image.save(waveform_file.name, waveform_file, save=False)
        analysis_record.spectrogram_image.save(spectrogram_file.name, spectrogram_file, save=False)

        # --- Feature Extraction ---
        features = extract_all_features(audio, sr)
        feature_summary = get_feature_summary(features)

        # --- ML Prediction ---
        pred_result = predict(
            features=features,
            model_path=str(settings.ML_MODEL_PATH),
            scaler_path=str(settings.ML_SCALER_PATH),
            model_version=settings.ML_MODEL_VERSION,
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        analysis_record.processing_duration_ms = elapsed_ms
        analysis_record.status = 'completed'
        analysis_record.save()

        # --- Save Prediction Result ---
        PredictionResult.objects.create(
            analysis=analysis_record,
            model_name=pred_result['model_name'],
            model_version=pred_result['model_version'],
            classification=pred_result['classification'],
            confidence_score=pred_result.get('confidence_score'),
            raw_scores=pred_result.get('raw_scores'),
            feature_summary=feature_summary,
            disclaimer=pred_result['disclaimer'],
        )

        logger.info(
            f"Analysis {analysis_record.id} complete: "
            f"{pred_result['classification']} in {elapsed_ms}ms"
        )

    except Exception as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        error_msg = str(exc)
        logger.error(f"Analysis {analysis_record.id} failed: {error_msg}")

        # Determine status
        from ml_pipeline.prediction import ModelNotAvailableError
        status = 'model_unavailable' if isinstance(exc, ModelNotAvailableError) else 'failed'
        classification = 'model_unavailable' if status == 'model_unavailable' else 'uncertain'

        analysis_record.status = status
        analysis_record.error_message = error_msg
        analysis_record.processing_duration_ms = elapsed_ms
        analysis_record.save()

        recording.status = 'error' if status == 'failed' else recording.status
        recording.processing_notes = error_msg[:500]
        recording.save(update_fields=['status', 'processing_notes'])

        # Still create a prediction result to record the failure
        from ml_pipeline.prediction import DISCLAIMER
        PredictionResult.objects.create(
            analysis=analysis_record,
            model_name='HeartSoundClassifier',
            model_version=settings.ML_MODEL_VERSION,
            classification=classification,
            confidence_score=None,
            raw_scores=None,
            feature_summary=None,
            disclaimer=DISCLAIMER,
        )
