"""Core context processors — provide global template variables."""
from django.conf import settings
from .models import SiteConfiguration


def site_context(request):
    """Inject site-wide context into every template."""
    config = SiteConfiguration.get_config()
    return {
        'SITE_NAME': getattr(settings, 'SITE_NAME', 'HeartSound AI'),
        'SITE_TAGLINE': getattr(settings, 'SITE_TAGLINE', 'AI-Powered Heart Sound Disease Detection System'),
        'SITE_VERSION': getattr(settings, 'SITE_VERSION', '1.0.0'),
        'MEDICAL_DISCLAIMER': config.medical_disclaimer,
        'CHATBOT_ENABLED': config.chatbot_enabled,
        'AI_PROVIDER': getattr(settings, 'AI_PROVIDER', ''),
    }
