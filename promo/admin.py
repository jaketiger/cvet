# promo/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import PromoCode


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    """
    Настройка админки для Промокодов.
    """

    # 1. ВКЛЮЧАЕМ КНОПКИ СВЕРХУ
    # Эта настройка заставляет Django добавить панель "Сохранить" над формой.
    # Нижняя панель тоже добавляется, но мы скрываем её через CSS.
    save_on_top = True

    # 2. ШАБЛОН ДЛЯ СПИСКА
    # Подключаем шаблон, который добавляет кнопку "Сохранить" над ТАБЛИЦЕЙ (списком).
    # Используем универсальный шаблон без лишних кнопок.
    change_list_template = "admin/change_list_save_top.html"

    # 3. ПОДКЛЮЧАЕМ СТИЛИ
    # Этот CSS делает кнопки красивыми и СКРЫВАЕТ нижние дубликаты.
    class Media:
        css = {
            'all': ('shop/css/admin_custom_buttons.css',)
        }

    # === НАСТРОЙКИ СПИСКА ===

    # Какие колонки показывать в таблице
    list_display = ['code', 'discount', 'status_badge', 'valid_from', 'valid_to', 'active']

    # Фильтры в правой боковой панели
    list_filter = ['active', 'valid_from', 'valid_to']

    # Поле поиска (ищет по коду)
    search_fields = ['code']

    # Позволяет менять галочку "Активен" прямо в таблице, не заходя в промокод
    list_editable = ['active']

    # === МЕТОДЫ ОТОБРАЖЕНИЯ ===

    def status_badge(self, obj):
        """
        Метод рисует красивый цветной статус (badge) в таблице.
        """
        now = timezone.now()

        # Если галочка 'active' снята вручную
        if not obj.active:
            return format_html(
                '<span style="color:white; background:#dc3545; padding:4px 10px; border-radius:12px; font-size:11px; font-weight:bold;">ОТКЛЮЧЕН</span>'
            )

        # Если дата начала еще не наступила
        if obj.valid_from and obj.valid_from > now:
            return format_html(
                '<span style="color:black; background:#ffc107; padding:4px 10px; border-radius:12px; font-size:11px; font-weight:bold;">ЖДЕТ НАЧАЛА</span>'
            )

        # Если дата окончания уже прошла
        if obj.valid_to and obj.valid_to < now:
            return format_html(
                '<span style="color:white; background:#6c757d; padding:4px 10px; border-radius:12px; font-size:11px; font-weight:bold;">ИСТЕК</span>'
            )

        # Если всё хорошо (Активен сейчас)
        return format_html(
            '<span style="color:white; background:#28a745; padding:4px 10px; border-radius:12px; font-size:11px; font-weight:bold;">АКТИВЕН</span>'
        )

    # Название колонки в шапке таблицы
    status_badge.short_description = "Статус"