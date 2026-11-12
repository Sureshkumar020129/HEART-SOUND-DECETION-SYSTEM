"""Heart analysis URL patterns."""
from django.urls import path
from . import views

app_name = 'heart_analysis'

urlpatterns = [
    path('upload/', views.upload_view, name='upload'),
    path('record/', views.browser_record_upload, name='browser_record'),
    path('<uuid:pk>/', views.result_view, name='result'),
    path('<uuid:pk>/detail/', views.detail_view, name='detail'),
    path('history/', views.history_view, name='history'),
    path('recording/<uuid:pk>/delete/', views.delete_recording, name='delete_recording'),
]
