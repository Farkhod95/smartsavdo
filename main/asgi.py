# main/asgi.py

import os, sys
from django.core.asgi import get_asgi_application

# BASE_DIR = "/home/host1836067/api.smartsavdo-group.com/htdocs/www"
# if BASE_DIR not in sys.path:
#     sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')

application = get_asgi_application()
