from django.contrib import admin
from .models import ChatSession, ChatMessage

class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ['role', 'content', 'source', 'timestamp']
    can_delete = False

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'is_active', 'started_at', 'last_active']
    list_filter = ['is_active', 'started_at']
    search_fields = ['user__username', 'id']
    inlines = [ChatMessageInline]

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'role', 'source', 'timestamp']
    list_filter = ['role', 'source', 'timestamp']
    search_fields = ['session__id', 'content']
