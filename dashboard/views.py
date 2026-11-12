"""Dashboard views — reads real database data only."""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

from heart_analysis.models import AnalysisRecord, PredictionResult
from assessments.models import HealthAssessment
from chatbot.models import ChatSession


@login_required
def dashboard_view(request):
    user = request.user
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    # Real counts from the database
    total_analyses = AnalysisRecord.objects.filter(user=user).count()
    recent_analyses = AnalysisRecord.objects.filter(user=user, created_at__gte=thirty_days_ago).count()
    total_assessments = HealthAssessment.objects.filter(user=user).count()

    # Classification breakdown (only completed analyses with predictions)
    completed_analyses = AnalysisRecord.objects.filter(user=user, status='completed')
    normal_count = PredictionResult.objects.filter(
        analysis__in=completed_analyses, classification='normal'
    ).count()
    abnormal_count = PredictionResult.objects.filter(
        analysis__in=completed_analyses, classification='abnormal'
    ).count()

    # Recent activity (last 5 analyses)
    recent_activity = AnalysisRecord.objects.filter(user=user).select_related(
        'recording', 'prediction'
    ).order_by('-created_at')[:5]

    # Latest assessment
    latest_assessment = HealthAssessment.objects.filter(user=user).order_by('-submitted_at').first()

    # Chart data: analyses per day over last 14 days
    chart_labels = []
    chart_values = []
    for i in range(13, -1, -1):
        day = (now - timedelta(days=i)).date()
        count = AnalysisRecord.objects.filter(
            user=user,
            created_at__date=day
        ).count()
        chart_labels.append(day.strftime('%b %d'))
        chart_values.append(count)

    context = {
        'total_analyses': total_analyses,
        'recent_analyses': recent_analyses,
        'total_assessments': total_assessments,
        'normal_count': normal_count,
        'abnormal_count': abnormal_count,
        'recent_activity': recent_activity,
        'latest_assessment': latest_assessment,
        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'has_data': total_analyses > 0,
    }
    return render(request, 'dashboard/dashboard.html', context)
