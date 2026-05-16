import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vcard_project.settings_dev')

from django.core.wsgi import get_wsgi_application  # noqa: E402
application = get_wsgi_application()
