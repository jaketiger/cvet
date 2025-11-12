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
    return {'site_settings': SiteSettings.get_solo()}

def footer_pages(request):
    """
    Добавляет список всех страниц из футера в контекст каждого шаблона.
    """
    # Убеждаемся, что ссылки в футере тоже отсортированы по полю 'order'
    return {'footer_pages': FooterPage.objects.all().order_by('order')}