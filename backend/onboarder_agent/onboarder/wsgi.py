"""
WSGI config for onboarder project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'onboarder.settings')

application = get_wsgi_application()
