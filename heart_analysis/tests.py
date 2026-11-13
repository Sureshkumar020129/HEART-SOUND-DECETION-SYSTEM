from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AnalysisResultViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='analysis-user',
            password='test-password',
        )
        self.client.force_login(self.user)

    def test_missing_analysis_redirects_to_history_with_message(self):
        response = self.client.get(
            reverse(
                'heart_analysis:result',
                kwargs={'pk': 'f8727b2d-a481-40b1-b763-a69b5db0fbe0'},
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('heart_analysis:history'))
        history_response = self.client.get(response.url)
        self.assertContains(history_response, 'This analysis is no longer available')
