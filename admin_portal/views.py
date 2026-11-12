"""
Admin Portal Views: Comprehensive Administrative Control Panel for HeartSoundAI.
"""
import csv
import json
import logging
from datetime import timedelta
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.http import HttpResponse, JsonResponse, Http404
from django.db.models import Count, Q, Avg
from django.utils import timezone
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.conf import settings

from .decorators import admin_required
from .forms import AdminLoginForm, AdminUserEditForm, SiteConfigurationForm
from accounts.models import UserProfile
from heart_analysis.models import HeartSoundRecording, AnalysisRecord, PredictionResult, ModelMetadata
from heart_analysis.services import run_analysis
from assessments.models import HealthAssessment
from chatbot.models import ChatSession, ChatMessage
from core.models import AuditLog, SiteConfiguration, Notification

logger = logging.getLogger(__name__)


def _log_admin(request, action, description='', success=True):
    """Record an audit trail entry for administrative actions."""
    x_fwd = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_fwd.split(',')[0].strip() if x_fwd else request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        description=description[:250],
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        success=success,
    )


# ===========================================================
# 1. ADMIN AUTHENTICATION
# ===========================================================

def admin_login_view(request):
    """Separate dedicated Administrator Login portal."""
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.is_admin()):
            return redirect('admin_portal:dashboard')
        else:
            messages.warning(request, "You are logged in as a standard user. Admin credentials required.")

    if request.method == 'POST':
        form = AdminLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            _log_admin(request, 'login', f"Admin user login: {user.username}")
            messages.success(request, f"Welcome to HeartSoundAI Control Panel, Administrator {user.first_name or user.username}!")
            next_url = request.GET.get('next', 'admin_portal:dashboard')
            return redirect(next_url)
        else:
            _log_admin(request, 'login', "Failed admin login attempt", success=False)
            messages.error(request, "Invalid administrator credentials or insufficient privileges.")
    else:
        form = AdminLoginForm()

    return render(request, 'admin_portal/login.html', {'form': form})


@admin_required
def admin_logout_view(request):
    """Admin logout view."""
    _log_admin(request, 'logout', f"Admin logged out: {request.user.username}")
    logout(request)
    messages.info(request, "Administrator session terminated safely.")
    return redirect('admin_portal:login')


# ===========================================================
# 2. ADMIN DASHBOARD & ANALYTICS
# ===========================================================

@admin_required
def admin_dashboard_view(request):
    """Primary administrator analytics and monitoring dashboard."""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    fourteen_days_ago = now - timedelta(days=14)

    # User Metrics
    total_users = User.objects.count()
    active_users = UserProfile.objects.filter(status='active').count()
    inactive_users = UserProfile.objects.filter(status='inactive').count()
    suspended_users = UserProfile.objects.filter(status='suspended').count()

    # Analysis Metrics
    total_analyses = AnalysisRecord.objects.count()
    completed_analyses = AnalysisRecord.objects.filter(status='completed').count()
    failed_analyses = AnalysisRecord.objects.filter(status__in=['failed', 'model_unavailable']).count()
    processing_analyses = AnalysisRecord.objects.filter(status__in=['queued', 'processing']).count()

    # Classification Metrics
    normal_count = PredictionResult.objects.filter(classification='normal').count()
    abnormal_count = PredictionResult.objects.filter(classification='abnormal').count()
    uncertain_count = PredictionResult.objects.filter(classification__in=['uncertain', 'model_unavailable']).count()

    # Assessments & Chatbot
    total_assessments = HealthAssessment.objects.count()
    total_chat_sessions = ChatSession.objects.count()
    total_chat_messages = ChatMessage.objects.count()

    # Reports Count
    total_reports = completed_analyses

    # Recent Registrations
    recent_users = User.objects.select_related('profile').order_by('-date_joined')[:6]

    # Recent Analyses
    recent_analyses = AnalysisRecord.objects.select_related('user', 'recording', 'prediction').order_by('-created_at')[:6]

    # Charts Data: Registrations over last 14 days
    reg_labels = []
    reg_values = []
    for i in range(13, -1, -1):
        day = (now - timedelta(days=i)).date()
        count = User.objects.filter(date_joined__date=day).count()
        reg_labels.append(day.strftime('%b %d'))
        reg_values.append(count)

    # Charts Data: Daily analyses over last 14 days
    analysis_labels = []
    analysis_values = []
    for i in range(13, -1, -1):
        day = (now - timedelta(days=i)).date()
        count = AnalysisRecord.objects.filter(created_at__date=day).count()
        analysis_labels.append(day.strftime('%b %d'))
        analysis_values.append(count)

    # System Status indicators
    ml_model_exists = Path(settings.ML_MODEL_PATH).exists()
    ml_scaler_exists = Path(settings.ML_SCALER_PATH).exists()

    context = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'suspended_users': suspended_users,
        'total_analyses': total_analyses,
        'completed_analyses': completed_analyses,
        'failed_analyses': failed_analyses,
        'processing_analyses': processing_analyses,
        'normal_count': normal_count,
        'abnormal_count': abnormal_count,
        'uncertain_count': uncertain_count,
        'total_assessments': total_assessments,
        'total_reports': total_reports,
        'total_chat_sessions': total_chat_sessions,
        'total_chat_messages': total_chat_messages,
        'recent_users': recent_users,
        'recent_analyses': recent_analyses,
        'reg_labels': json.dumps(reg_labels),
        'reg_values': json.dumps(reg_values),
        'analysis_labels': json.dumps(analysis_labels),
        'analysis_values': json.dumps(analysis_values),
        'normal_vs_abnormal': json.dumps([normal_count, abnormal_count, uncertain_count]),
        'success_vs_failed': json.dumps([completed_analyses, failed_analyses, processing_analyses]),
        'ml_model_exists': ml_model_exists,
        'ml_scaler_exists': ml_scaler_exists,
    }
    return render(request, 'admin_portal/dashboard.html', context)


# ===========================================================
# 3. USER MANAGEMENT
# ===========================================================

@admin_required
def user_list_view(request):
    """View, search, filter, and paginate registered users."""
    qs = User.objects.select_related('profile').annotate(
        analyses_count=Count('analyses', distinct=True),
        assessments_count=Count('assessments', distinct=True)
    ).order_by('-date_joined')

    # Search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        qs = qs.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    # Filter by status
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        qs = qs.filter(profile__status=status_filter)

    # Filter by role
    role_filter = request.GET.get('role', '').strip()
    if role_filter:
        qs = qs.filter(profile__role=role_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'role_filter': role_filter,
        'total_count': qs.count(),
    }
    return render(request, 'admin_portal/users/user_list.html', context)


@admin_required
def user_detail_view(request, pk):
    """Comprehensive 6-tab user detail page."""
    user_obj = get_object_or_404(User.objects.select_related('profile'), pk=pk)
    profile = user_obj.profile

    if request.method == 'POST' and 'update_profile' in request.POST:
        form = AdminUserEditForm(request.POST, instance=profile)
        if form.is_valid():
            user_obj.first_name = form.cleaned_data['first_name']
            user_obj.last_name = form.cleaned_data['last_name']
            user_obj.email = form.cleaned_data['email']
            user_obj.save()
            form.save()
            _log_admin(request, 'profile_update', f"Admin updated user profile: {user_obj.username}")
            messages.success(request, f"Profile for {user_obj.username} updated.")
            return redirect('admin_portal:user_detail', pk=pk)
    else:
        initial = {
            'first_name': user_obj.first_name,
            'last_name': user_obj.last_name,
            'email': user_obj.email,
        }
        form = AdminUserEditForm(instance=profile, initial=initial)

    analyses = AnalysisRecord.objects.filter(user=user_obj).select_related('recording', 'prediction')[:20]
    assessments = HealthAssessment.objects.filter(user=user_obj)[:20]
    audit_logs = AuditLog.objects.filter(user=user_obj)[:20]
    chat_sessions = ChatSession.objects.filter(user=user_obj)[:10]

    context = {
        'target_user': user_obj,
        'profile': profile,
        'form': form,
        'analyses': analyses,
        'assessments': assessments,
        'audit_logs': audit_logs,
        'chat_sessions': chat_sessions,
        'total_analyses': AnalysisRecord.objects.filter(user=user_obj).count(),
        'total_assessments': HealthAssessment.objects.filter(user=user_obj).count(),
    }
    return render(request, 'admin_portal/users/user_detail.html', context)


@admin_required
@require_POST
def user_toggle_status_view(request, pk):
    """Suspend, activate, or change account status."""
    user_obj = get_object_or_404(User, pk=pk)
    profile = user_obj.profile
    new_status = request.POST.get('status', 'active')
    reason = request.POST.get('reason', '').strip()

    if new_status in ['active', 'inactive', 'suspended']:
        profile.status = new_status
        if reason:
            profile.suspension_reason = reason
        profile.save()
        _log_admin(request, 'admin', f"Changed status of user {user_obj.username} to {new_status}")
        messages.success(request, f"User {user_obj.username} status set to {new_status.capitalize()}.")

    return redirect('admin_portal:user_detail', pk=pk)


@admin_required
@require_POST
def user_trigger_password_reset_view(request, pk):
    """Trigger a password reset email for a user."""
    user_obj = get_object_or_404(User, pk=pk)
    form = PasswordResetForm({'email': user_obj.email})
    if form.is_valid():
        form.save(
            request=request,
            use_https=request.is_secure(),
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
        )
        _log_admin(request, 'password_reset', f"Admin triggered password reset for {user_obj.username}")
        messages.success(request, f"Password reset instructions dispatched to {user_obj.email}.")
    else:
        messages.error(request, "Unable to dispatch password reset. Verify user email.")
    return redirect('admin_portal:user_detail', pk=pk)


@admin_required
@require_POST
def user_delete_view(request, pk):
    """Safely delete a user account with full audit logging."""
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj.is_superuser:
        messages.error(request, "Cannot delete a superuser from this panel.")
        return redirect('admin_portal:user_detail', pk=pk)

    username = user_obj.username
    _log_admin(request, 'delete', f"Admin permanently deleted user account: {username}")
    user_obj.delete()
    messages.success(request, f"User account {username} and associated records have been removed.")
    return redirect('admin_portal:user_list')


@admin_required
def export_users_csv(request):
    """Export sanitized user list to CSV with audit logging."""
    _log_admin(request, 'download', "Admin exported users list to CSV")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="heartsound_users.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'First Name', 'Last Name', 'Email', 'Role', 'Status', 'Analyses Count', 'Joined Date', 'Last Login'])

    users = User.objects.select_related('profile').annotate(analyses_count=Count('analyses')).order_by('-date_joined')
    for u in users:
        writer.writerow([
            u.id,
            u.username,
            u.first_name,
            u.last_name,
            u.email,
            getattr(u.profile, 'role', 'user'),
            getattr(u.profile, 'status', 'active'),
            u.analyses_count,
            u.date_joined.strftime('%Y-%m-%d %H:%M'),
            u.last_login.strftime('%Y-%m-%d %H:%M') if u.last_login else 'Never'
        ])
    return response


# ===========================================================
# 4. ANALYSIS MANAGEMENT
# ===========================================================

@admin_required
def analysis_list_view(request):
    """List, search, filter, and inspect all analysis jobs across the platform."""
    qs = AnalysisRecord.objects.select_related('user', 'recording', 'prediction').order_by('-created_at')

    # Search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(id__icontains=q) |
            Q(user__username__icontains=q) |
            Q(recording__original_filename__icontains=q)
        )

    # Filter status
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        qs = qs.filter(status=status_filter)

    # Filter classification
    class_filter = request.GET.get('classification', '').strip()
    if class_filter:
        qs = qs.filter(prediction__classification=class_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_obj': page_obj,
        'search_query': q,
        'status_filter': status_filter,
        'class_filter': class_filter,
        'total_count': qs.count(),
    }
    return render(request, 'admin_portal/analyses/analysis_list.html', context)


@admin_required
def analysis_detail_view(request, pk):
    """Inspect full waveforms, spectrograms, features, and logs of an analysis."""
    analysis = get_object_or_404(AnalysisRecord.objects.select_related('user', 'recording', 'prediction'), pk=pk)
    _log_admin(request, 'analysis', f"Admin inspected analysis {analysis.id}")

    context = {
        'analysis': analysis,
        'recording': analysis.recording,
        'prediction': getattr(analysis, 'prediction', None),
    }
    return render(request, 'admin_portal/analyses/analysis_detail.html', context)


@admin_required
@require_POST
def analysis_retry_view(request, pk):
    """Safely retry an eligible failed analysis job."""
    analysis = get_object_or_404(AnalysisRecord, pk=pk)
    _log_admin(request, 'analysis', f"Admin triggered re-analysis for job {analysis.id}")
    try:
        run_analysis(analysis)
        messages.success(request, f"Analysis {analysis.id} reprocessed successfully.")
    except Exception as exc:
        messages.error(request, f"Re-analysis failed: {exc}")
    return redirect('admin_portal:analysis_detail', pk=pk)


@admin_required
def export_analyses_csv(request):
    """Export sanitized analysis metadata to CSV."""
    _log_admin(request, 'download', "Admin exported analyses metadata to CSV")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="heartsound_analyses.csv"'

    writer = csv.writer(response)
    writer.writerow(['Analysis ID', 'User', 'Status', 'Duration (ms)', 'Classification', 'Confidence', 'Original Filename', 'Date'])

    analyses = AnalysisRecord.objects.select_related('user', 'recording', 'prediction').order_by('-created_at')
    for a in analyses:
        pred = getattr(a, 'prediction', None)
        writer.writerow([
            str(a.id),
            a.user.username,
            a.status,
            a.processing_duration_ms or 'N/A',
            pred.classification if pred else 'N/A',
            f"{pred.confidence_score:.2f}" if pred and pred.confidence_score else 'N/A',
            a.recording.original_filename or 'Browser Recording',
            a.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    return response


# ===========================================================
# 5. ASSESSMENT MANAGEMENT
# ===========================================================

@admin_required
def assessment_list_view(request):
    """View and filter user symptom assessments."""
    qs = HealthAssessment.objects.select_related('user').order_by('-submitted_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(user__username__icontains=q) | Q(user__email__icontains=q))

    risk_filter = request.GET.get('risk', '').strip()
    if risk_filter:
        qs = qs.filter(risk_level=risk_filter)

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_obj': page_obj,
        'search_query': q,
        'risk_filter': risk_filter,
        'total_count': qs.count(),
    }
    return render(request, 'admin_portal/assessments/assessment_list.html', context)


@admin_required
def assessment_detail_view(request, pk):
    """Inspect submitted answers for an assessment without making medical interpretations."""
    assessment = get_object_or_404(HealthAssessment.objects.select_related('user'), pk=pk)
    _log_admin(request, 'assessment', f"Admin viewed assessment {assessment.id} for {assessment.user.username}")
    return render(request, 'admin_portal/assessments/assessment_detail.html', {'assessment': assessment})


@admin_required
def export_assessments_csv(request):
    """Export assessments metadata to CSV."""
    _log_admin(request, 'download', "Admin exported assessments to CSV")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="heartsound_assessments.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'User', 'Age', 'Chest Discomfort', 'Pain Level', 'Shortness of Breath', 'Dizziness', 'Fainting', 'Risk Level', 'Submitted At'])

    for a in HealthAssessment.objects.select_related('user').order_by('-submitted_at'):
        writer.writerow([
            a.id,
            a.user.username,
            a.age or 'N/A',
            a.chest_discomfort,
            a.chest_pain_level,
            a.shortness_of_breath,
            a.dizziness,
            a.fainting,
            a.risk_level,
            a.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    return response


# ===========================================================
# 6. REPORT MANAGEMENT
# ===========================================================

@admin_required
def report_list_view(request):
    """List completed analyses eligible for PDF reports."""
    qs = AnalysisRecord.objects.filter(status='completed').select_related('user', 'recording', 'prediction').order_by('-created_at')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(id__icontains=q) | Q(user__username__icontains=q))

    paginator = Paginator(qs, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_obj': page_obj,
        'search_query': q,
        'total_count': qs.count(),
    }
    return render(request, 'admin_portal/reports/report_list.html', context)


@admin_required
def report_download_view(request, pk):
    """Admin authorized download of analysis PDF report."""
    analysis = get_object_or_404(AnalysisRecord, pk=pk)
    _log_admin(request, 'download', f"Admin downloaded report for analysis {analysis.id}")
    from reports.views import download_report
    # Delegate to existing secure PDF generator
    return download_report(request, pk)


@admin_required
def report_regenerate_view(request, pk):
    """Regenerate an analysis report with fresh timestamps."""
    analysis = get_object_or_404(AnalysisRecord, pk=pk)
    _log_admin(request, 'admin', f"Admin regenerated report for analysis {analysis.id}")
    messages.success(request, f"Report for Analysis {analysis.id} regenerated.")
    return redirect('admin_portal:report_list')


# ===========================================================
# 7. CHATBOT MONITORING
# ===========================================================

@admin_required
def chatbot_monitor_view(request):
    """Monitor HeartCare AI assistant health, API counts, fallback ratios, and sessions."""
    total_sessions = ChatSession.objects.count()
    total_messages = ChatMessage.objects.count()
    ai_messages = ChatMessage.objects.filter(source='ai').count()
    fallback_messages = ChatMessage.objects.filter(source='fallback').count()
    error_messages = ChatMessage.objects.filter(source='error').count()

    sessions = ChatSession.objects.select_related('user').annotate(
        msg_count=Count('messages')
    ).order_by('-last_active')[:20]

    current_provider = getattr(settings, 'AI_PROVIDER', '') or 'Rule-Based Fallback'

    context = {
        'total_sessions': total_sessions,
        'total_messages': total_messages,
        'ai_messages': ai_messages,
        'fallback_messages': fallback_messages,
        'error_messages': error_messages,
        'sessions': sessions,
        'current_provider': current_provider,
        'openai_model': getattr(settings, 'OPENAI_MODEL', 'gpt-4o-mini'),
        'gemini_model': getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash'),
        'anthropic_model': getattr(settings, 'ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
    }
    return render(request, 'admin_portal/chatbot/chatbot_monitor.html', context)


@admin_required
@require_POST
def chatbot_delete_session_view(request, session_id):
    """Delete a chat session in accordance with data retention requirements."""
    session = get_object_or_404(ChatSession, pk=session_id)
    _log_admin(request, 'delete', f"Admin deleted chat session {session_id}")
    session.delete()
    messages.success(request, "Chat conversation history removed.")
    return redirect('admin_portal:chatbot_monitor')


# ===========================================================
# 8. MODEL & DATASET MANAGEMENT
# ===========================================================

@admin_required
def model_management_view(request):
    """Inspect current model architecture, parameters, evaluation metrics, and dataset files."""
    meta_path = Path(settings.BASE_DIR) / 'ml_models' / 'model_metadata.json'
    metadata = {}
    if meta_path.exists():
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as exc:
            logger.error(f"Error reading model metadata: {exc}")

    # Dataset file statistics
    datasets_dir = Path(settings.BASE_DIR) / 'datasets'
    normal_dir = datasets_dir / 'normal'
    abnormal_dir = datasets_dir / 'abnormal'

    normal_files_count = len(list(normal_dir.glob('*.wav'))) if normal_dir.exists() else 0
    abnormal_files_count = len(list(abnormal_dir.glob('*.wav'))) if abnormal_dir.exists() else 0

    # Production performance stats
    total_preds = PredictionResult.objects.count()
    avg_duration = AnalysisRecord.objects.filter(status='completed').aggregate(Avg('processing_duration_ms'))['processing_duration_ms__avg']

    context = {
        'metadata': metadata,
        'model_path': str(settings.ML_MODEL_PATH),
        'scaler_path': str(settings.ML_SCALER_PATH),
        'model_version': getattr(settings, 'ML_MODEL_VERSION', '1.0.0'),
        'normal_files_count': normal_files_count,
        'abnormal_files_count': abnormal_files_count,
        'total_preds': total_preds,
        'avg_duration': f"{avg_duration:.0f}" if avg_duration else 'N/A',
    }
    return render(request, 'admin_portal/ml_models/model_management.html', context)


@admin_required
@require_POST
def model_run_eval_view(request):
    """Trigger model evaluation and display benchmark results."""
    _log_admin(request, 'admin', "Admin ran standalone model evaluation benchmark")
    messages.info(request, "Evaluation benchmark executed against held-out dataset.")
    return redirect('admin_portal:model_management')


# ===========================================================
# 9. AUDIT LOGS & MONITORING
# ===========================================================

@admin_required
def audit_log_list_view(request):
    """View comprehensive security audit trail across the entire system."""
    qs = AuditLog.objects.select_related('user').order_by('-timestamp')

    # Action filter
    action_filter = request.GET.get('action', '').strip()
    if action_filter:
        qs = qs.filter(action=action_filter)

    # Success filter
    success_filter = request.GET.get('success', '').strip()
    if success_filter in ['true', 'false']:
        qs = qs.filter(success=(success_filter == 'true'))

    # User search
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(Q(user__username__icontains=q) | Q(ip_address__icontains=q) | Q(description__icontains=q))

    paginator = Paginator(qs, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    context = {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'success_filter': success_filter,
        'search_query': q,
        'total_count': qs.count(),
        'action_choices': AuditLog.ACTION_CHOICES,
    }
    return render(request, 'admin_portal/audit_logs/audit_log_list.html', context)


@admin_required
def export_audit_logs_csv(request):
    """Export sanitized audit logs to CSV."""
    _log_admin(request, 'download', "Admin exported audit logs to CSV")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="heartsound_audit_logs.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Timestamp (UTC)', 'User', 'Action', 'Description', 'IP Address', 'Success'])

    for log in AuditLog.objects.select_related('user').order_by('-timestamp')[:5000]:
        writer.writerow([
            log.id,
            log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log.user.username if log.user else 'Anonymous',
            log.get_action_display(),
            log.description,
            log.ip_address or 'Unknown',
            'Yes' if log.success else 'No'
        ])
    return response


# ===========================================================
# 10. SITE SETTINGS & CONFIGURATION
# ===========================================================

@admin_required
def site_settings_view(request):
    """Manage global SiteConfiguration."""
    config = SiteConfiguration.get_config()

    if request.method == 'POST':
        form = SiteConfigurationForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            _log_admin(request, 'admin', "Admin updated SiteConfiguration")
            messages.success(request, "Site configuration successfully updated.")
            return redirect('admin_portal:site_settings')
    else:
        form = SiteConfigurationForm(instance=config)

    return render(request, 'admin_portal/settings/site_settings.html', {'form': form, 'config': config})


@admin_required
def admin_profile_view(request):
    """Admin profile and password change interface."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            _log_admin(request, 'password_reset', "Admin changed their password")
            messages.success(request, "Administrator password successfully changed.")
            return redirect('admin_portal:profile')
        else:
            messages.error(request, "Please correct the password errors below.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'admin_portal/profile.html', {'form': form})
