from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class DashboardPageTests(TestCase):
    def test_dashboard_does_not_render_module_sidebar(self):
        user = User.objects.create_user(username='dashboard-user', password='test-password')
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'dashboard-sidebar')
        self.assertContains(response, 'Welcome back')
        self.assertContains(
            response,
            '<a class="topbar-breadcrumb-root text-decoration-none" href="/">HeartSoundAI</a>',
        )
