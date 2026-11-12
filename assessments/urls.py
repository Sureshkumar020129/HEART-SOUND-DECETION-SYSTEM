from django.urls import path
from . import views
app_name = 'assessments'
urlpatterns = [
    path('', views.assessment_view, name='assessment'),
    path('<int:pk>/result/', views.assessment_result, name='result'),
    path('history/', views.assessment_history, name='history'),
]
