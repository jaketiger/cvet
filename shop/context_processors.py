# shop/context_processors.py

from .models import Category, SiteSettings, FooterPage

def categories(request):
    """
    Добавляет список всех категорий в контекст каждого шаблона.
    """
    return {'categories': Category.objects.all().order_by('order')}

def site_settings(request):
    """
    Добавляет объект настроек сайта в контекст.
    Используем get_solo() для надежности.
    """
    try:
        return {'site_settings': SiteSettings.get_solo()}
    except:
        return {'site_settings': None}

def footer_pages(request):
    """
    Добавляет список страниц футера.
    """
    return {'footer_pages': FooterPage.objects.all().order_by('order')}