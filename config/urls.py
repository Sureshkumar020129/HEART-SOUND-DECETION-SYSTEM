"""
URL configuration for AI-Powered Heart Sound Disease Detection System.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    # Core / Landing
    path('', include('core.urls')),
    # User accounts
    path('accounts/', include('accounts.urls')),
    # Dashboard
    path('dashboard/', include('dashboard.urls')),
    # Heart analysis
    path('analysis/', include('heart_analysis.urls')),
    # Health assessments
    path('assessment/', include('assessments.urls')),
    # AI Chatbot
    path('chatbot/', include('chatbot.urls')),
    # Reports
    path('reports/', include('reports.urls')),
]

# Serve media files in development (never use this in production)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler403 = 'core.views.error_403'
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'
