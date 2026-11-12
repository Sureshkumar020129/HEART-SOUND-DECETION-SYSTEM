"""Assessment views."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .forms import HealthAssessmentForm
from .models import HealthAssessment
from core.models import AuditLog


def _log(request, action, description=''):
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x.split(',')[0].strip() if x else request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(user=request.user, action=action, description=description,
                            ip_address=ip, user_agent=request.META.get('HTTP_USER_AGENT', '')[:512])


@login_required
def assessment_view(request):
    if request.method == 'POST':
        form = HealthAssessmentForm(request.POST)
        if form.is_valid():
            assessment = form.save(commit=False)
            assessment.user = request.user
            assessment.save()
            _log(request, 'assessment', f'Risk level: {assessment.risk_level}')
            try:
                from core.models import Notification
                notif_type = 'danger' if assessment.risk_level == 'seek_urgent' else ('warning' if assessment.risk_level == 'high' else 'info')
                Notification.objects.create(
                    user=request.user,
                    title="Health Assessment Completed",
                    message=f"Your cardiovascular symptom assessment was evaluated with risk level: {assessment.get_risk_level_display()}.",
                    notification_type=notif_type,
                    link_url=f"/assessment/{assessment.pk}/"
                )
            except Exception:
                pass
            return redirect('assessments:result', pk=assessment.pk)
        else:
            messages.error(request, 'Please correct the errors and resubmit.')
    else:
        form = HealthAssessmentForm()
    return render(request, 'assessments/assessment.html', {'form': form})


@login_required
def assessment_result(request, pk):
    assessment = get_object_or_404(HealthAssessment, pk=pk, user=request.user)
    return render(request, 'assessments/result.html', {'assessment': assessment})


@login_required
def assessment_history(request):
    qs = HealthAssessment.objects.filter(user=request.user)
    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'assessments/history.html', {'page_obj': page_obj})
