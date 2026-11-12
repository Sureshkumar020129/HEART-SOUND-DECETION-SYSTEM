"""Chatbot models: session and messages."""
import uuid
from django.db import models
from django.contrib.auth.models import User


class ChatSession(models.Model):
    """A single conversation session between a user and HeartCare AI."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions', null=True, blank=True)
    session_key = models.CharField(max_length=100, blank=True)  # for anonymous sessions
    started_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-last_active']

    def __str__(self):
        return f"ChatSession {self.id} ({'user: ' + self.user.username if self.user else 'anon'})"


class ChatMessage(models.Model):
    """An individual message in a chat session."""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    SOURCE_CHOICES = [
        ('ai', 'AI Provider'),
        ('fallback', 'Rule-Based Fallback'),
        ('error', 'Error Response'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='ai')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role}: {self.content[:60]}..."
