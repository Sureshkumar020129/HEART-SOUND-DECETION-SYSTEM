import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile
from core.models import SiteConfiguration

class Command(BaseCommand):
    help = "Initializes default administrator account and site configuration"

    def add_arguments(self, parser):
        parser.add_argument('--username', default='admin', help='Admin username')
        parser.add_argument('--email', default='admin@heartsound.ai', help='Admin email')
        parser.add_argument('--password', default='Admin12345!', help='Admin password')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"User '{username}' already exists."))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='System',
            last_name='Administrator'
        )
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = 'admin'
        profile.data_consent = True
        profile.save()

        SiteConfiguration.get_config()

        self.stdout.write(self.style.SUCCESS(
            f"Superuser '{username}' created successfully!\n"
            f"Username: {username}\n"
            f"Password: {password}\n"
            f"Email: {email}"
        ))
