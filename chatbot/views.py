"""Chatbot views."""
import json
import logging
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.conf import settings
from .models import ChatSession, ChatMessage
from .services import get_chat_response
from core.models import AuditLog

logger = logging.getLogger(__name__)


@login_required
def chatbot_view(request):
    """Main chatbot page."""
    # Get or create session
    session, _ = ChatSession.objects.get_or_create(
        user=request.user,
        is_active=True,
        defaults={'session_key': ''}
    )
    messages_qs = session.messages.order_by('timestamp')[:settings.CHATBOT_MAX_HISTORY]

    suggested_prompts = [
        "How do I upload a heart sound?",
        "What does an abnormal classification mean?",
        "Explain my analysis report.",
        "What is a heart murmur?",
        "How accurate is the AI model?",
        "What is an MFCC?",
    ]

    return render(request, 'chatbot/chatbot.html', {
        'session': session,
        'messages': list(messages_qs),
        'suggested_prompts': suggested_prompts,
        'ai_provider': getattr(settings, 'AI_PROVIDER', ''),
    })


@login_required
@require_POST
@csrf_protect
def send_message(request):
    """AJAX endpoint: receive user message, return AI response."""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not user_message:
        return JsonResponse({'error': 'Message cannot be empty'}, status=400)
    if len(user_message) > 2000:
        return JsonResponse({'error': 'Message too long (max 2000 chars)'}, status=400)

    # Get or create session
    session, _ = ChatSession.objects.get_or_create(
        user=request.user,
        is_active=True,
        defaults={'session_key': ''}
    )

    # Build conversation history for context
    history = list(
        session.messages.order_by('-timestamp', '-pk')
        .values('role', 'content')[:settings.CHATBOT_MAX_HISTORY]
    )
    history.reverse()

    # Save user message
    ChatMessage.objects.create(session=session, role='user', content=user_message, source='ai')

    # Get AI response
    result = get_chat_response(user_message, history)
    response_text = result['response']
    source = result['source']
    is_emergency = result['is_emergency']

    # Save assistant message
    ChatMessage.objects.create(session=session, role='assistant', content=response_text, source=source)

    # Audit log (no message content — only action type)
    x = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x.split(',')[0].strip() if x else request.META.get('REMOTE_ADDR')
    AuditLog.objects.create(user=request.user, action='chatbot', description=f'source={source}',
                            ip_address=ip, user_agent=request.META.get('HTTP_USER_AGENT', '')[:512])

    return JsonResponse({
        'response': response_text,
        'source': source,
        'is_emergency': is_emergency,
        'is_fallback': (source == 'fallback'),
    })


@login_required
@require_POST
def clear_chat(request):
    """Clear the user's current chat session."""
    ChatSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
    return JsonResponse({'status': 'cleared'})
