"""Core middleware: audit logging and security utilities."""
import logging
from .models import AuditLog

logger = logging.getLogger(__name__)


class AuditLogMiddleware:
    """Attach client IP and log administrative actions or critical errors."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.client_ip = self._get_client_ip(request)
        response = self.get_response(request)

        # Log security-relevant responses like forbidden access
        if response.status_code == 403 and request.user.is_authenticated:
            try:
                AuditLog.objects.create(
                    user=request.user,
                    action='admin',
                    description=f"403 Forbidden on {request.path}",
                    ip_address=request.client_ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                    success=False
                )
            except Exception:
                pass

        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
