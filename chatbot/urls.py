from django.urls import path
from . import views
app_name = 'chatbot'
urlpatterns = [
    path('', views.chatbot_view, name='chatbot'),
    path('api/message/', views.send_message, name='send_message'),
    path('api/clear/', views.clear_chat, name='clear_chat'),
]
