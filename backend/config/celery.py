import os
from celery import Celery

# 1. Указываем Джанге, где искать файл настроек settings.py
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 2. Создаем сам объект приложения Celery и даем ему имя проекта
app = Celery('uralmeb')

# 3. Говорим Celery брать свои настройки прямо из твоего settings.py.
# Настройки для Селери в settings.py будут начинаться с префикса CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# 4. Автоматически ищем фоновые задачи (таски) по всему проекту.
# Celery сама пробежится по твоим приложениям и найдет файлы tasks.py
app.autodiscover_tasks()
