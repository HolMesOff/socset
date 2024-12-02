import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socset.settings')

# Render-specific: Используем порт из переменной окружения
port = os.getenv('PORT', 8000)
application = get_wsgi_application()