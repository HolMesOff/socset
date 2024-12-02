import os
from django.core.management import execute_from_command_line

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "socset.settings")
    try:
        from django.core.management.commands.runserver import Command as runserver
        port = os.getenv("PORT", "8000")  # Используем порт из окружения или 8000 по умолчанию
        runserver.default_port = port
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line()
