# shop/context_processors.py
from .models import Category, SiteSettings

def categories(request):
    """
    Добавляет список всех категорий в контекст каждого шаблона.
    """
    return {'categories': Category.objects.all()}

def site_settings(request):
    """
    Добавляет объект настроек сайта в контекст каждого шаблона.
    """
    return {'site_settings': SiteSettings.get_solo()}