"""Heart analysis models: recording, analysis, and prediction result."""
import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator


def heart_sound_upload_path(instance, filename):
    """Store files in user-specific subdirectories with UUID names."""
    ext = os.path.splitext(filename)[1].lower()
    new_name = f"{uuid.uuid4().hex}{ext}"
    return f"heart_sounds/{instance.user.id}/{new_name}"


class HeartSoundRecording(models.Model):
    """An uploaded or browser-recorded heart sound file."""
    SOURCE_CHOICES = [
        ('upload', 'File Upload'),
        ('browser', 'Browser Recording'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending Processing'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recordings')
    original_filename = models.CharField(max_length=255, blank=True)
    audio_file = models.FileField(
        upload_to=heart_sound_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['wav', 'flac', 'mp3', 'ogg', 'aiff'])]
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='upload')
    file_size_bytes = models.PositiveIntegerField(default=0)
    duration_seconds = models.FloatField(null=True, blank=True)
    sample_rate = models.IntegerField(null=True, blank=True)
    channels = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    processing_notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', 'uploaded_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Recording {self.id} by {self.user.username} ({self.status})"

    def delete(self, *args, **kwargs):
        """Delete the file from disk when the model is deleted."""
        if self.audio_file and os.path.isfile(self.audio_file.path):
            os.remove(self.audio_file.path)
        super().delete(*args, **kwargs)


class AnalysisRecord(models.Model):
    """Tracks a single analysis job for a recording."""
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('model_unavailable', 'Model Unavailable'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analyses')
    recording = models.ForeignKey(HeartSoundRecording, on_delete=models.CASCADE, related_name='analyses')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='queued')
    # Processing metadata
    processing_duration_ms = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    # Waveform / spectrogram stored as base64 or file path
    waveform_image = models.ImageField(upload_to='analysis_plots/', null=True, blank=True)
    spectrogram_image = models.ImageField(upload_to='analysis_plots/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Analysis {self.id} — {self.status}"


class PredictionResult(models.Model):
    """The ML model's output for a given analysis."""
    CLASSIFICATION_CHOICES = [
        ('normal', 'Normal'),
        ('abnormal', 'Abnormal'),
        ('uncertain', 'Uncertain'),
        ('model_unavailable', 'Model Not Available'),
    ]

    analysis = models.OneToOneField(AnalysisRecord, on_delete=models.CASCADE, related_name='prediction')
    # Model metadata at time of inference
    model_name = models.CharField(max_length=100, default='HeartSoundClassifier')
    model_version = models.CharField(max_length=50)
    # Result
    classification = models.CharField(max_length=30, choices=CLASSIFICATION_CHOICES)
    confidence_score = models.FloatField(null=True, blank=True,
        help_text='Model probability output (0–1). Not a clinical probability.')
    raw_scores = models.JSONField(null=True, blank=True,
        help_text='Per-class probability vector from the model.')
    feature_summary = models.JSONField(null=True, blank=True,
        help_text='Summary of extracted features (for audit / reproducibility).')
    # Disclaimer — always shown with results
    disclaimer = models.TextField(
        default=(
            'This classification is produced by a machine-learning model for '
            'research and educational screening purposes only. It is NOT a '
            'clinical diagnosis. Please consult a qualified healthcare professional.'
        )
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Prediction for {self.analysis.id}: {self.classification}"


class ModelMetadata(models.Model):
    """Tracks ML model versions and evaluation results."""
    name = models.CharField(max_length=100)
    version = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    model_file_path = models.CharField(max_length=255, blank=True)
    scaler_file_path = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=False)
    # Evaluation metrics — stored from evaluation.py
    accuracy = models.FloatField(null=True, blank=True)
    precision = models.FloatField(null=True, blank=True)
    recall = models.FloatField(null=True, blank=True)
    f1_score = models.FloatField(null=True, blank=True)
    sensitivity = models.FloatField(null=True, blank=True)
    specificity = models.FloatField(null=True, blank=True)
    training_dataset = models.CharField(max_length=255, blank=True)
    training_samples = models.IntegerField(null=True, blank=True)
    evaluation_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Model Metadata'
        verbose_name_plural = 'Model Metadata'

    def __str__(self):
        return f"{self.name} v{self.version} ({'active' if self.is_active else 'inactive'})"
