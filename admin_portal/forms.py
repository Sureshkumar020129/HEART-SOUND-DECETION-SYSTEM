"""
Admin Portal Forms.
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from accounts.models import UserProfile
from core.models import SiteConfiguration


class AdminLoginForm(AuthenticationForm):
    """Admin-specific login form ensuring credentials belong to an administrator."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Administrator Username',
            'id': 'adminUsername'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': 'Administrator Password',
            'id': 'adminPassword'
        })

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        is_admin_user = (
            user.is_staff or
            user.is_superuser or
            (hasattr(user, 'profile') and user.profile.is_admin())
        )
        if not is_admin_user:
            raise forms.ValidationError(
                "Access restricted: This account does not possess administrator credentials.",
                code='not_admin'
            )
        if hasattr(user, 'profile') and user.profile.status != 'active':
            raise forms.ValidationError(
                f"Administrator account is {user.profile.status}.",
                code='account_disabled'
            )


class AdminUserEditForm(forms.ModelForm):
    """Allows administrators to edit permissible user profile and status fields."""
    first_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserProfile
        fields = ['role', 'status', 'suspension_reason', 'phone', 'date_of_birth', 'email_notifications']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'suspension_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reason if inactive or suspended'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SiteConfigurationForm(forms.ModelForm):
    """Allows administrators to manage site-wide settings."""
    class Meta:
        model = SiteConfiguration
        fields = ['site_name', 'maintenance_mode', 'allow_registration', 'max_analyses_per_day', 'chatbot_enabled', 'medical_disclaimer']
        widgets = {
            'site_name': forms.TextInput(attrs={'class': 'form-control'}),
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'allow_registration': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_analyses_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
            'chatbot_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'medical_disclaimer': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
