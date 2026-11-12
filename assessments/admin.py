from django.contrib import admin
from .models import HealthAssessment

@admin.register(HealthAssessment)
class HealthAssessmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'age', 'risk_level', 'chest_discomfort', 'shortness_of_breath', 'submitted_at']
    list_filter = ['risk_level', 'chest_discomfort', 'shortness_of_breath', 'submitted_at']
    search_fields = ['user__username', 'additional_notes']
