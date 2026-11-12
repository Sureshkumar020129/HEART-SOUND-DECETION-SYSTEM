"""
Admin Portal URL Routing.
"""
from django.urls import path
from . import views

app_name = 'admin_portal'

urlpatterns = [
    # Authentication
    path('login/', views.admin_login_view, name='login'),
    path('logout/', views.admin_logout_view, name='logout'),

    # Dashboard
    path('', views.admin_dashboard_view, name='dashboard'),
    path('dashboard/', views.admin_dashboard_view, name='dashboard'),

    # User Management
    path('users/', views.user_list_view, name='user_list'),
    path('users/<int:pk>/', views.user_detail_view, name='user_detail'),
    path('users/<int:pk>/status/', views.user_toggle_status_view, name='user_toggle_status'),
    path('users/<int:pk>/reset-password/', views.user_trigger_password_reset_view, name='user_trigger_password_reset'),
    path('users/<int:pk>/delete/', views.user_delete_view, name='user_delete'),
    path('users/export/csv/', views.export_users_csv, name='export_users_csv'),

    # Analysis Management
    path('analyses/', views.analysis_list_view, name='analysis_list'),
    path('analyses/<uuid:pk>/', views.analysis_detail_view, name='analysis_detail'),
    path('analyses/<uuid:pk>/retry/', views.analysis_retry_view, name='analysis_retry'),
    path('analyses/export/csv/', views.export_analyses_csv, name='export_analyses_csv'),

    # Assessment Management
    path('assessments/', views.assessment_list_view, name='assessment_list'),
    path('assessments/<int:pk>/', views.assessment_detail_view, name='assessment_detail'),
    path('assessments/export/csv/', views.export_assessments_csv, name='export_assessments_csv'),

    # Report Management
    path('reports/', views.report_list_view, name='report_list'),
    path('reports/<uuid:pk>/download/', views.report_download_view, name='report_download'),
    path('reports/<uuid:pk>/regenerate/', views.report_regenerate_view, name='report_regenerate'),

    # Chatbot Monitoring
    path('chatbot/', views.chatbot_monitor_view, name='chatbot_monitor'),
    path('chatbot/sessions/<uuid:session_id>/delete/', views.chatbot_delete_session_view, name='chatbot_delete_session'),

    # ML Model & Dataset Management
    path('models/', views.model_management_view, name='model_management'),
    path('models/evaluate/', views.model_run_eval_view, name='model_evaluate'),

    # Audit Logs
    path('audit-logs/', views.audit_log_list_view, name='audit_log_list'),
    path('audit-logs/export/csv/', views.export_audit_logs_csv, name='export_audit_logs_csv'),

    # Settings & Profile
    path('settings/', views.site_settings_view, name='site_settings'),
    path('profile/', views.admin_profile_view, name='profile'),
]
