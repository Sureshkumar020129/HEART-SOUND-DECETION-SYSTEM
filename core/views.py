"""Core app views: landing page, about, how it works, errors, help, privacy, terms."""
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Notification


def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')


def how_it_works(request):
    return render(request, 'how_it_works.html')


def help_faq(request):
    return render(request, 'help_faq.html')


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


def terms_disclaimer(request):
    return render(request, 'terms_disclaimer.html')


# Custom error views
def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)


def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    return render(request, 'errors/500.html', status=500)


@login_required
def notifications_list(request):
    """View all notifications for the logged in user."""
    notifications = Notification.objects.filter(user=request.user)
    paginator = Paginator(notifications, 15)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'core/notifications.html', {'page_obj': page_obj})


@login_required
@require_POST
def mark_notification_read(request, pk):
    """Mark a single notification as read."""
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    if notif.link_url:
        return redirect(notif.link_url)
    return redirect('core:notifications')


@login_required
@require_POST
def mark_all_notifications_read(request):
    """Mark all notifications as read for current user."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'ok'})
    return redirect('core:notifications')
