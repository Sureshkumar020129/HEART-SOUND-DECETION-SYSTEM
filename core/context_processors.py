"""Core context processors — provide global template variables."""
from django.conf import settings
from .models import SiteConfiguration


def site_context(request):
    """Inject site-wide context into every template."""
    config = SiteConfiguration.get_config()
    unread_notifications = []
    unread_count = 0
    is_admin = False

    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            from .models import Notification
            unread_qs = Notification.objects.filter(user=request.user, is_read=False)
            unread_count = unread_qs.count()
            unread_notifications = list(unread_qs.order_by('-created_at')[:5])
        except Exception:
            pass

        if hasattr(request.user, 'profile') and request.user.profile.is_admin():
            is_admin = True
        elif request.user.is_staff or request.user.is_superuser:
            is_admin = True

    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'HeartSound AI'),
        'SITE_TAGLINE': getattr(settings, 'SITE_TAGLINE', 'AI-Powered Heart Sound Disease Detection System'),
        'SITE_VERSION': getattr(settings, 'SITE_VERSION', '1.0.0'),
        'MEDICAL_DISCLAIMER': config.medical_disclaimer,
        'CHATBOT_ENABLED': config.chatbot_enabled,
        'AI_PROVIDER': getattr(settings, 'AI_PROVIDER', ''),
        'unread_notifications_count': unread_count,
        'recent_notifications': unread_notifications,
        'is_portal_admin': is_admin,
    }
