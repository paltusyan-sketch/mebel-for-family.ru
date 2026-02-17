

# app1/context_processors.py


def site_settings(request):
    from .models import Setting
    """
    Добавляет объект настроек сайта в контекст каждого запроса.
    """
    try:
        settings = Setting.objects.get()
    except Setting.DoesNotExist:
        settings = None
    except Setting.MultipleObjectsReturned:
        # Если вдруг их несколько, берем первый (наш save() метод это предотвращает)
        settings = Setting.objects.first()

    return {'site_settings': settings}
