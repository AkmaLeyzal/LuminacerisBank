# authentication/management/commands/create_default_roles.py
from django.core.management.base import BaseCommand
from authentication.models import Role

class Command(BaseCommand):
    help = 'Create default roles'

    def handle(self, *args, **options):
        # Create User role
        user_role, created = Role.objects.get_or_create(
            name='USER',
            defaults={
                'description': 'Default role for registered users',
                'permissions': {
                    'permissions': [
                        'view_profile',
                        'edit_profile',
                        'make_transaction'
                    ]
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created USER role'))

        # Create Admin role
        admin_role, created = Role.objects.get_or_create(
            name='ADMIN',
            defaults={
                'description': 'Administrator role',
                'permissions': {
                    'permissions': [
                        'view_profile',
                        'edit_profile',
                        'make_transaction',
                        'manage_users',
                        'manage_roles'
                    ]
                }
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Successfully created ADMIN role'))