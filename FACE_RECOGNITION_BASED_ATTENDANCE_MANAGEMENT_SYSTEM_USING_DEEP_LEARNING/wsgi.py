"""
WSGI config for FACE_RECOGNITION_BASED_ATTENDANCE_MANAGEMENT_SYSTEM_USING_DEEP_LEARNING project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FACE_RECOGNITION_BASED_ATTENDANCE_MANAGEMENT_SYSTEM_USING_DEEP_LEARNING.settings')

application = get_wsgi_application()
