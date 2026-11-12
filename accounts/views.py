"""Accounts views: register, login, logout, profile, password reset."""
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from django.utils import timezone
from django.urls import reverse_lazy
from .forms import RegistrationForm, CustomLoginForm, UserProfileForm
from .models import UserProfile
from core.models import AuditLog, Notification

logger = logging.getLogger(__name__)


def _log_action(request, action, description='', success=True):
    """Helper to record an audit log entry."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action=action,
        description=description,
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
        success=success,
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            # Ensure regular user status and consent
            profile = user.profile
            profile.role = 'user'
            profile.status = 'active'
            profile.data_consent = True
            profile.data_consent_at = timezone.now()
            profile.save()

            # Create welcome notification
            Notification.objects.create(
                user=user,
                title="Welcome to HeartSound AI",
                message="Your account is active. You can start uploading heart sound recordings or take a cardiovascular symptom assessment.",
                notification_type="success",
                link_url="/dashboard/"
            )

            login(request, user)
            _log_action(request, 'register', f'New user registered: {user.username}')
            messages.success(request, f'Welcome, {user.first_name}! Your account has been created.')
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            _log_action(request, 'login', f'User: {user.username}')
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next', 'dashboard:dashboard')
            return redirect(next_url)
        else:
            _log_action(request, 'login', 'Failed login attempt', success=False)
            messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    if request.method == 'POST':
        _log_action(request, 'logout', f'User: {request.user.username}')
        logout(request)
        messages.info(request, 'You have been logged out.')
        return redirect('core:home')
    return render(request, 'accounts/logout_confirm.html')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            # Update User model fields
            request.user.first_name = form.cleaned_data.get('first_name', request.user.first_name)
            request.user.last_name = form.cleaned_data.get('last_name', request.user.last_name)
            request.user.email = form.cleaned_data.get('email', request.user.email)
            request.user.save()
            form.save()
            _log_action(request, 'profile_update', f'Profile updated for {request.user.username}')
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = UserProfileForm(instance=profile, initial=initial)

    # Gather stats
    from heart_analysis.models import AnalysisRecord
    from assessments.models import HealthAssessment
    analysis_count = AnalysisRecord.objects.filter(user=request.user).count()
    assessment_count = HealthAssessment.objects.filter(user=request.user).count()

    context = {
        'form': form,
        'profile': profile,
        'analysis_count': analysis_count,
        'assessment_count': assessment_count,
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def change_password_view(request):
    """Allow user to change password securely."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            _log_action(request, 'password_reset', 'User changed their password')
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def delete_account_view(request):
    """Allow user to request account deletion."""
    if request.method == 'POST':
        user = request.user
        _log_action(request, 'delete', f'User deleted own account: {user.username}')
        logout(request)
        user.delete()
        messages.success(request, 'Your account and personal data have been permanently deleted.')
        return redirect('core:home')
    return render(request, 'accounts/delete_account_confirm.html')


# Password Reset Views using Django built-ins
class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    success_url = reverse_lazy('accounts:password_reset_done')
    email_template_name = 'accounts/password_reset_email.html'


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'
