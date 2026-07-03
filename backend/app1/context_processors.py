

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


def seo_settings(request):
    from .models import SEO

    try:
        seo = SEO.objects.get()
    except SEO.DoesNotExist:
        seo = None
    except SEO.MultipleObjectsReturned:
        # Если вдруг их несколько, берем первый (наш save() метод это предотвращает)
        seo = SEO.objects.first()

    return {'seo': seo}


def debug_status(request):
    from django.conf import settings
    """
    Прокидывает статус режима отладки (True/False) напрямую в шаблоны.
    """
    return {'debug': settings.DEBUG}
