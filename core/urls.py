"""Core URL patterns."""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('help/', views.help_faq, name='help'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_disclaimer, name='terms'),
]
