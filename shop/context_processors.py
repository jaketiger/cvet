# shop/context_processors.py

from .models import Category, SiteSettings, FooterPage

def categories(request):
    """
    Добавляет список всех категорий в контекст каждого шаблона,
    отсортированный по полю 'order'.
    """
    return {'categories': Category.objects.all().order_by('order')}

def site_settings(request):
    """
    Добавляет объект настроек сайта в контекст каждого шаблона.
    """
    # ▼▼▼ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Загружаем настройки напрямую из базы, в обход кэша django-solo ▼▼▼
    try:
        # Мы напрямую обращаемся к базе данных для получения единственной записи настроек.
        # Это гарантирует, что мы всегда получаем самые свежие данные, которые вы сохранили в админке.
        settings_obj = SiteSettings.objects.get(pk=1)
    except SiteSettings.DoesNotExist:
        # Если по какой-то причине настроек в базе нет, возвращаем пустоту, чтобы сайт не сломался.
        settings_obj = None
    return {'site_settings': settings_obj}
    # ▲▲▲ КОНЕЦ ИЗМЕНЕНИЯ ▲▲▲


def footer_pages(request):
    """
    Добавляет список всех страниц из футера в контекст каждого шаблона.
    """
    # Убеждаемся, что ссылки в футере тоже отсортированы по полю 'order'
    return {'footer_pages': FooterPage.objects.all().order_by('order')}