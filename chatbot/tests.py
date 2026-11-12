import json

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch

from .models import ChatMessage, ChatSession


class SendMessageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='chat-test-user', password='test-password')
        self.client.force_login(self.user)

    @override_settings(AI_PROVIDER='')
    def test_message_uses_fallback_and_persists_chat(self):
        response = self.client.post(
            reverse('chatbot:send_message'),
            data=json.dumps({'message': 'How do I upload a heart sound?'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['source'], 'fallback')
        self.assertIn('upload a heart sound recording', payload['response'])
        self.assertEqual(
            list(ChatMessage.objects.values_list('role', flat=True)),
            ['user', 'assistant'],
        )

    @override_settings(AI_PROVIDER='', CHATBOT_MAX_HISTORY=2)
    def test_message_history_is_limited_to_most_recent_entries(self):
        session = ChatSession.objects.create(user=self.user, is_active=True)
        ChatMessage.objects.create(session=session, role='user', content='oldest')
        ChatMessage.objects.create(session=session, role='assistant', content='middle')
        ChatMessage.objects.create(session=session, role='user', content='newest')

        with patch(
            'chatbot.views.get_chat_response',
            return_value={
                'response': 'Test response',
                'source': 'ai',
                'is_emergency': False,
            },
        ) as get_response:
            response = self.client.post(
                reverse('chatbot:send_message'),
                data=json.dumps({'message': 'current'}),
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            get_response.call_args.args[1],
            [
                {'role': 'assistant', 'content': 'middle'},
                {'role': 'user', 'content': 'newest'},
            ],
        )
