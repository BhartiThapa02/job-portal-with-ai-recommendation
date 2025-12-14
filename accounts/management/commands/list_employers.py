"""
Management command to list all employer accounts with their details
Usage: python manage.py list_employers
"""
from django.core.management.base import BaseCommand
from accounts.models import User


class Command(BaseCommand):
    help = 'List all employer accounts with their details'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Filter by email address',
        )
        parser.add_argument(
            '--approved',
            action='store_true',
            help='Show only approved employers',
        )
        parser.add_argument(
            '--unapproved',
            action='store_true',
            help='Show only unapproved employers',
        )

    def handle(self, *args, **options):
        employers = User.objects.filter(user_type='employer')
        
        if options['email']:
            employers = employers.filter(email__icontains=options['email'])
        
        if options['approved']:
            employers = employers.filter(is_approved=True)
        
        if options['unapproved']:
            employers = employers.filter(is_approved=False)
        
        if not employers.exists():
            self.stdout.write(self.style.WARNING('No employer accounts found.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\nFound {employers.count()} employer account(s):\n'))
        self.stdout.write('-' * 100)
        self.stdout.write(f'{"ID":<5} {"Email":<35} {"Username":<20} {"Approved":<10} {"Verified":<10} {"Phone":<15}')
        self.stdout.write('-' * 100)
        
        for employer in employers:
            self.stdout.write(
                f'{employer.id:<5} '
                f'{employer.email:<35} '
                f'{employer.username or "N/A":<20} '
                f'{"Yes" if employer.is_approved else "No":<10} '
                f'{"Yes" if employer.is_email_verified else "No":<10} '
                f'{employer.phone or "N/A":<15}'
            )
        
        self.stdout.write('-' * 100)
        self.stdout.write(self.style.SUCCESS('\nTo reset a password, use Django admin or run:'))
        self.stdout.write('python manage.py shell')
        self.stdout.write('>>> from accounts.models import User')
        self.stdout.write('>>> user = User.objects.get(email="employer@example.com")')
        self.stdout.write('>>> user.set_password("newpassword123")')
        self.stdout.write('>>> user.save()')

