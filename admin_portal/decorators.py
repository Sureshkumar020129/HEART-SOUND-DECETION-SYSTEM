"""
Security decorators for the Admin Portal.
Strictly enforce server-side role and staff permissions.
"""
from functools import wraps
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden
from django.urls import reverse
from core.models import AuditLog


def admin_required(view_func):
    """
    Decorator that checks whether the user is authenticated and is an administrator
    (is_staff, is_superuser, or profile.role == 'admin').
    Unauthenticated users are redirected to the admin login page.
    Authenticated non-admin users receive a 403 Forbidden response.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            login_url = reverse('admin_portal:login')
            return redirect(f"{login_url}?next={request.path}")

        is_admin_user = (
            request.user.is_staff or
            request.user.is_superuser or
            (hasattr(request.user, 'profile') and request.user.profile.is_admin())
        )

        if not is_admin_user:
            # Audit log unauthorized access attempt
            x_fwd = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_fwd.split(',')[0].strip() if x_fwd else request.META.get('REMOTE_ADDR')
            AuditLog.objects.create(
                user=request.user,
                action='admin',
                description=f"Unauthorized access attempt to {request.path}",
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:512],
                success=False
            )
            return render(request, 'errors/403.html', status=403)

        return view_func(request, *args, **kwargs)

    return _wrapped_view
