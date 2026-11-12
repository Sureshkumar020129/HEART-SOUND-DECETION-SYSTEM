"""Core app views: landing page, about, how it works, errors, help, privacy, terms."""
from django.shortcuts import render
from django.http import HttpResponse


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
