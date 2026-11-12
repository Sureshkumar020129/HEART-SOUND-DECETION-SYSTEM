from django.contrib import admin
from .models import HeartSoundRecording, AnalysisRecord, PredictionResult, ModelMetadata

@admin.register(HeartSoundRecording)
class HeartSoundRecordingAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'original_filename', 'source', 'duration_seconds', 'status', 'uploaded_at']
    list_filter = ['source', 'status', 'uploaded_at']
    search_fields = ['user__username', 'original_filename']

@admin.register(AnalysisRecord)
class AnalysisRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'processing_duration_ms', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'id']

@admin.register(PredictionResult)
class PredictionResultAdmin(admin.ModelAdmin):
    list_display = ['analysis', 'model_name', 'classification', 'confidence_score', 'created_at']
    list_filter = ['classification', 'model_name', 'created_at']
    search_fields = ['analysis__id', 'analysis__user__username']

@admin.register(ModelMetadata)
class ModelMetadataAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'is_active', 'accuracy', 'f1_score', 'sensitivity', 'specificity', 'created_at']
    list_filter = ['is_active', 'created_at']
