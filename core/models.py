"""
Core app models: AuditLog and global configuration.
"""
from django.db import models
from django.contrib.auth.models import User


class AuditLog(models.Model):
    """Tracks important user actions for security and compliance."""
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('register', 'Register'),
        ('upload', 'Audio Upload'),
        ('analysis', 'Analysis Run'),
        ('download', 'Report Download'),
        ('delete', 'Record Deleted'),
        ('admin', 'Admin Action'),
        ('profile_update', 'Profile Update'),
        ('assessment', 'Assessment Submitted'),
        ('chatbot', 'Chatbot Interaction'),
        ('password_reset', 'Password Reset'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    # Description must NOT include personal health data
    description = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user} — {self.action} — {self.timestamp:%Y-%m-%d %H:%M}"


class SiteConfiguration(models.Model):
    """Single-row site-wide configuration (admin editable)."""
    site_name = models.CharField(max_length=100, default='HeartSound AI')
    maintenance_mode = models.BooleanField(default=False)
    allow_registration = models.BooleanField(default=True)
    max_analyses_per_day = models.PositiveIntegerField(default=20)
    chatbot_enabled = models.BooleanField(default=True)
    medical_disclaimer = models.TextField(
        default=(
            "This application is a research and educational screening-support tool only. "
            "It is NOT a substitute for professional medical advice, diagnosis, or treatment. "
            "Always consult a qualified healthcare provider for any medical concerns."
        )
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Site Configuration'

    def __str__(self):
        return f"Site Configuration (updated {self.updated_at:%Y-%m-%d})"

    def save(self, *args, **kwargs):
        # Enforce single row
        self.__class__.objects.exclude(id=self.id).delete()
        super().save(*args, **kwargs)

    @classmethod
    def get_config(cls):
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class Notification(models.Model):
    """In-app user and administrative notifications."""
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('danger', 'Urgent / Alert'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    link_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"
