"""
WSGI config for Guardian Agent project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'guardian.settings')

application = get_wsgi_application()
