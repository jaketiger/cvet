# shop/middleware.py

import pytz
from django.utils import timezone
from django.core.cache import cache
from .models import SiteSettings

class SiteTimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Пробуем взять из кэша
        tzname = cache.get('active_site_timezone')

        if not tzname:
            try:
                # 2. Если нет в кэше, берем из БД
                settings = SiteSettings.get_solo()
                tzname = settings.site_time_zone
                # Кэшируем на час
                cache.set('active_site_timezone', tzname, 3600)
            except:
                tzname = 'Europe/Moscow'

        # 3. Активируем зону
        if tzname:
            timezone.activate(pytz.timezone(tzname))
        else:
            timezone.deactivate()

        response = self.get_response(request)
        return response