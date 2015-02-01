from django.conf import settings


DB_IS_POSTGRES = 'postgresql' in settings.DATABASES['default'].get('ENGINE', '')
