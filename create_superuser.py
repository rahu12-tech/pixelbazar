#!/usr/bin/env python
import os
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bazarbackend.settings')
    django.setup()
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    # Create superuser if not exists
    if not User.objects.filter(email='admin@pixelbazar.com').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@pixelbazar.com',
            password='admin123456'
        )
        print("✅ Superuser created successfully!")
    else:
        print("✅ Superuser already exists!")