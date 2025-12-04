# orders/admin.py

from django.contrib import admin, messages
from django import forms
from .models import Order, OrderItem
from django.urls import reverse, path
from django.shortcuts import redirect
from django.utils.html import format_html
from django_q.tasks import async_task
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
import json
from decimal import Decimal

from shop.models import SiteSettings


class OrderItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price'].required = False


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    form = OrderItemForm
    fields = ('product', 'price', 'quantity')
    autocomplete_fields = ['product']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'type_display',
        'first_name', 'last_name',
        'recipient_display',
        'delivery_date_fmt',
        'get_delivery_time_display',
        'status', 'paid',
        'delivery_option',
        'postcard_status_column',
        'get_postcard_price_display',
        'get_total_cost_display',
        'created',
    )

    list_filter = ('is_one_click', 'status', 'paid', 'created', 'updated', 'delivery_date', 'delivery_option')
    search_fields = (
        'id',
        'first_name', 'last_name', 'email', 'phone',
        'recipient_name', 'recipient_phone', 'address',
        'items__product__name', 'items__product__sku'
    )

    # Статус можно менять прямо в списке
    list_editable = ['status']

    inlines = [OrderItemInline]

    readonly_fields = (
        'id', 'user', 'created', 'updated',
        'get_items_cost_display',
        'get_postcard_cost_display',
        'get_delivery_cost_display',
        'get_total_cost_display',
        'postcard_preview', 'custom_postcard_preview', 'is_one_click',
        'delivery_info_display',
        'cost_breakdown_display',
    )

    # === ВКЛЮЧАЕМ КНОПКИ СОХРАНЕНИЯ НАВЕРХУ ===
    save_on_top = True

    # Шаблон списка (для кнопки автосохранения)
    change_list_template = "admin/orders/order/change_list.html"

    fieldsets = (
        ('Основная информация', {
            'fields': ('status', 'is_one_click', 'paid', 'delivery_option', 'delivery_cost')
        }),
        ('Заказчик', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Получатель (если отличается)', {
            'fields': ('recipient_name', 'recipient_phone'),
            'description': 'Заполняется только если клиент выбрал опцию "Другой человек".'
        }),
        ('Адрес доставки', {
            'fields': ('address', 'postal_code', 'city')
        }),

        ('📅 Дата и Время доставки (Установлено клиентом)', {
            'fields': ('delivery_date', 'delivery_time'),
            'description': 'Данные установлены клиентом при оформлении. Изменяйте их только после согласования с покупателем!'
        }),

        ('Открытка', {
            'fields': (
                'postcard',
                'postcard_preview',
                'custom_postcard_image',
                'custom_postcard_preview',
                'postcard_text'
            )
        }),
        ('Информация о доставке', {
            'fields': ('delivery_info_display',),
            'classes': ('collapse',),
        }),
        ('Стоимость', {
            'fields': (
                'get_items_cost_display',
                'get_postcard_cost_display',
                'get_delivery_cost_display',
                'cost_breakdown_display',
                'get_total_cost_display',
                'created',
                'updated'
            )
        }),
    )

    # === ПОДКЛЮЧЕНИЕ СТИЛЕЙ И СКРИПТОВ ===
    @property
    def media(self):
        media = super().media
        extra_css = {'all': ['shop/css/admin_custom_buttons.css']}
        extra_js = []

        try:
            if SiteSettings.get_solo().enable_admin_autosave:
                extra_js.append('shop/js/admin_auto_save.js')
        except:
            pass

        return media + forms.Media(css=extra_css, js=extra_js)

    # === URLS ===
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # 1. AJAX переключатель автосохранения
            path('toggle-autosave/', self.admin_site.admin_view(self.toggle_autosave_view),
                 name='order_toggle_autosave'),

            # 2. AJAX обновление статуса
            path('ajax/update-status/', self.admin_site.admin_view(self.update_status_view),
                 name='order_ajax_update_status'),

            # 3. Кнопки отправки писем
            path('<path:object_id>/send_confirmation/', self.admin_site.admin_view(self.send_confirmation_email_view),
                 name='orders_order_send_confirmation'),
            path('<path:object_id>/send_status/', self.admin_site.admin_view(self.send_status_email_view),
                 name='orders_order_send_status'),

            # 4. Старая кнопка notify (оставляем для совместимости)
            path('<path:object_id>/notify/', self.admin_site.admin_view(self.notify_customer_full),
                 name='order_notify_customer_full'),
        ]
        return custom_urls + urls

    # === VIEW: ПЕРЕКЛЮЧЕНИЕ АВТОСОХРАНЕНИЯ ===
    def toggle_autosave_view(self, request):
        settings = SiteSettings.get_solo()
        settings.enable_admin_autosave = not settings.enable_admin_autosave
        settings.save()

        status_msg = "ВКЛЮЧЕНО ✅" if settings.enable_admin_autosave else "ВЫКЛЮЧЕНО ❌"
        self.message_user(request, f"Автосохранение статусов {status_msg}")
        return redirect(request.META.get('HTTP_REFERER', 'admin:orders_order_changelist'))

    # === VIEW: AJAX ОБНОВЛЕНИЕ СТАТУСА ===
    @method_decorator(csrf_protect)
    def update_status_view(self, request):
        if request.method == 'POST':
            try:
                data = json.loads(request.body)
                order_id = data.get('id')
                new_status = data.get('status')

                order = Order.objects.get(id=order_id)
                order.status = new_status
                order.save(update_fields=['status'])

                return JsonResponse(
                    {'success': True, 'message': f'Заказ #{order_id}: Статус изменен на {order.get_status_display()}'})
            except Order.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Заказ не найден'})
            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        return JsonResponse({'success': False, 'error': 'Invalid method'})

    # === КОНТЕКСТ ДЛЯ СПИСКА ЗАКАЗОВ ===
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            extra_context['autosave_enabled'] = SiteSettings.get_solo().enable_admin_autosave
        except:
            extra_context['autosave_enabled'] = False
        return super().changelist_view(request, extra_context=extra_context)

    # === МЕТОДЫ ОТОБРАЖЕНИЯ ===

    def type_display(self, obj):
        if obj.is_one_click:
            return format_html(
                '<span style="color: orange; font-weight: bold; font-size: 1.2em;" title="Быстрый заказ">⚡ 1-Click</span>')
        return format_html('<span style="color: #666;" title="Обычный заказ">🛒 Корзина</span>')

    type_display.short_description = "Тип"

    def delivery_date_fmt(self, obj):
        if obj.delivery_date:
            return obj.delivery_date.strftime('%d.%m.%Y')
        return "-"

    delivery_date_fmt.short_description = "Дата доставки"

    def get_delivery_time_display(self, obj):
        """ИСПРАВЛЕНО: Красивое отображение времени доставки в админке"""
        if obj.delivery_time == 'asap':
            return format_html('<span style="color: orange; font-weight: bold;">🚀 Как можно быстрее</span>')
        return obj.delivery_time

    get_delivery_time_display.short_description = "Время доставки"

    def recipient_display(self, obj):
        if obj.recipient_name:
            return format_html('<span style="color: #e67e22;">🎁 {}</span>', obj.recipient_name)
        return "👤 Заказчик"

    recipient_display.short_description = "Получатель"

    def postcard_status_column(self, obj):
        """ИСПРАВЛЕНО: Отображение статуса открытки с учетом всех комбинаций"""
        if obj.custom_postcard_image:
            # Кастомное фото
            if obj.postcard:
                # Свое фото + платная основа
                if obj.postcard_final_price > 0:
                    return format_html(
                        '<span style="color: purple; font-weight: bold;">📸 Своё фото</span><br>'
                        '<small>+ основа "{}" ({} руб.)</small>',
                        obj.postcard.title, obj.postcard_final_price
                    )
                else:
                    return format_html(
                        '<span style="color: purple; font-weight: bold;">📸 Своё фото</span><br>'
                        '<small>+ основа "{}" (Бесплатно)</small>',
                        obj.postcard.title
                    )
            else:
                # Только свое фото
                if obj.postcard_final_price > 0:
                    return format_html(
                        '<span style="color: purple; font-weight: bold;">📸 Своё фото ({} руб.)</span>',
                        obj.postcard_final_price
                    )
                else:
                    return format_html('<span style="color: purple; font-weight: bold;">📸 Своё фото (Бесплатно)</span>')
        elif obj.postcard:
            # Обычная открытка
            if obj.postcard_final_price > 0:
                return format_html(
                    '<span style="color: green;">💌 {} ({} руб.)</span>',
                    obj.postcard.title, obj.postcard_final_price
                )
            else:
                return format_html('<span style="color: #666;">💌 {} (Бесплатно)</span>', obj.postcard.title)
        return "-"

    postcard_status_column.short_description = "Открытка"

    def get_postcard_price_display(self, obj):
        """Цена открытки в списке заказов"""
        if obj.postcard_final_price > 0:
            return format_html('<span style="color: #28a745; font-weight: bold;">{} руб.</span>',
                               obj.postcard_final_price)
        elif obj.custom_postcard_image or obj.postcard:
            return "Бесплатно"
        return "-"

    get_postcard_price_display.short_description = "Цена открытки"

    def get_postcard_cost_display(self, obj):
        """Стоимость открытки в детальном просмотре"""
        if obj.postcard_final_price > 0:
            if obj.custom_postcard_image and obj.postcard:
                return format_html(
                    '<span style="color: #28a745; font-weight: bold;">{} руб.</span><br>'
                    '<small style="color: #666;">(Своё фото + основа "{}")</small>',
                    obj.postcard_final_price,
                    obj.postcard.title
                )
            elif obj.custom_postcard_image:
                return format_html(
                    '<span style="color: #28a745; font-weight: bold;">{} руб.</span><br>'
                    '<small style="color: #666;">(Своё фото)</small>',
                    obj.postcard_final_price
                )
            else:
                return format_html(
                    '<span style="color: #28a745; font-weight: bold;">{} руб.</span><br>'
                    '<small style="color: #666;">(Открытка "{}")</small>',
                    obj.postcard_final_price,
                    obj.postcard.title if obj.postcard else ''
                )
        elif obj.custom_postcard_image:
            if obj.postcard:
                return format_html(
                    "Бесплатно<br>"
                    '<small style="color: #666;">(Своё фото + основа "{}")</small>',
                    obj.postcard.title
                )
            else:
                return "Бесплатно (Своё фото)"
        elif obj.postcard:
            return "Бесплатно"
        return "-"

    get_postcard_cost_display.short_description = "Стоимость открытки"

    def get_items_cost_display(self, obj):
        return f"{obj.get_items_cost()} руб."

    get_items_cost_display.short_description = "Стоимость товаров"

    def get_delivery_cost_display(self, obj):
        """Стоимость доставки"""
        if obj.delivery_cost > 0:
            return f"{obj.delivery_cost} руб."
        return "Бесплатно"

    get_delivery_cost_display.short_description = "Стоимость доставки"

    def delivery_info_display(self, obj):
        """Информация о доставке с темно-синим фоном #3e5265"""
        if obj.delivery_option == 'delivery':
            # Создаем части HTML
            index_html = ''
            if obj.postal_code:
                index_html = format_html(
                    '<div style="margin-bottom: 5px; color: #ecf0f1;">'
                    '<strong style="color: #bdc3c7;">Индекс:</strong> '
                    '<span style="color: #ffffff;">{}</span>'
                    '</div>',
                    obj.postal_code
                )

            delivery_cost_html = format_html(
                '<span style="color: #ffffff;">{} руб.</span>',
                obj.delivery_cost
            ) if obj.delivery_cost > 0 else format_html('<span style="color: #2ecc71;">Бесплатно</span>')

            info = format_html(
                '<div style="background: #3e5265; padding: 15px; border-radius: 8px; border: 1px solid #2c3e50;">'
                '<div style="display: flex; align-items: center; margin-bottom: 10px;">'
                '<span style="font-size: 1.5em; margin-right: 10px; color: #ffffff;">🚚</span>'
                '<strong style="color: #ffffff;">Доставка курьером</strong>'
                '</div>'
                '<div style="margin-bottom: 5px; color: #ecf0f1;">'
                '<strong style="color: #bdc3c7;">Адрес:</strong> '
                '<span style="color: #ffffff;">{}</span>'
                '</div>'
                '<div style="margin-bottom: 5px; color: #ecf0f1;">'
                '<strong style="color: #bdc3c7;">Город:</strong> '
                '<span style="color: #ffffff;">{}</span>'
                '</div>'
                '{}'
                '<div style="margin-bottom: 5px; color: #ecf0f1;">'
                '<strong style="color: #bdc3c7;">Время:</strong> '
                '<span style="color: #ffffff;">{}</span>'
                '</div>'
                '<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #4a6572; color: #ecf0f1;">'
                '<strong style="color: #bdc3c7;">Стоимость доставки:</strong> {}'
                '</div>'
                '</div>',
                obj.address,
                obj.city,
                index_html,
                obj.get_delivery_time_display(),
                delivery_cost_html
            )
        else:
            info = format_html(
                '<div style="background: #3e5265; padding: 15px; border-radius: 8px; border: 1px solid #2c3e50;">'
                '<div style="display: flex; align-items: center; margin-bottom: 10px;">'
                '<span style="font-size: 1.5em; margin-right: 10px; color: #ffffff;">🏪</span>'
                '<strong style="color: #ffffff;">Самовывоз</strong>'
                '</div>'
                '<div style="margin-bottom: 5px; color: #ecf0f1;">'
                '<strong style="color: #bdc3c7;">Время получения:</strong> '
                '<span style="color: #ffffff;">{}</span>'
                '</div>'
                '<div style="color: #bdc3c7; font-size: 0.9em;">'
                'Клиент заберёт заказ самостоятельно из магазина'
                '</div>'
                '</div>',
                obj.get_delivery_time_display()
            )
        return info

    delivery_info_display.short_description = "Информация о доставке"

    def cost_breakdown_display(self, obj):
        """ИСПРАВЛЕНО: Детальная разбивка стоимости с темно-синим фоном #3e5265"""
        items_cost = obj.get_items_cost()
        discount_amount = obj.get_discount_amount()
        postcard_cost = obj.postcard_final_price
        delivery_cost = obj.delivery_cost
        total = obj.get_total_cost()

        # Форматируем суммы без лишних нулей
        def format_price(price):
            formatted = f"{price:.2f} руб."
            return formatted.replace('.00', '')

        # Скидка
        discount_html = ''
        if discount_amount > 0:
            discount_html = format_html(
                '<div style="display: flex; justify-content: space-between; margin-bottom: 5px; color: #2ecc71;">'
                '<span>Скидка:</span>'
                '<span>-{}</span>'
                '</div>',
                format_price(discount_amount)
            )

        # Открытка с детализацией
        postcard_detail = ''
        if postcard_cost > 0:
            if obj.custom_postcard_image:
                detail = "Своё фото"
                if obj.postcard:
                    detail += f" + основа '{obj.postcard.title}'"
            elif obj.postcard:
                detail = f"Открытка '{obj.postcard.title}'"
            else:
                detail = "Открытка"

            postcard_detail = format_html(
                '<div style="font-size: 0.85em; color: #bdc3c7; margin-left: 10px;">{}</div>',
                detail
            )

        return format_html(
            '<div style="background: #3e5265; padding: 15px; border-radius: 8px; border: 1px solid #2c3e50;">'
            '<div style="display: flex; justify-content: space-between; margin-bottom: 5px; color: #ecf0f1;">'
            '<span>Товары:</span>'
            '<span style="color: #ffffff;">{}</span>'
            '</div>'
            '{}'
            '<div style="display: flex; justify-content: space-between; margin-bottom: 5px; color: #ecf0f1;">'
            '<span>Доставка:</span>'
            '<span style="color: #ffffff;">{}</span>'
            '</div>'
            '<div style="display: flex; justify-content: space-between; margin-bottom: 5px; color: #ecf0f1;">'
            '<span>Открытка:</span>'
            '<span style="color: #ffffff;">{}</span>'
            '</div>'
            '{}'
            '<hr style="margin: 10px 0; border-color: #4a6572;">'
            '<div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1em; color: #ecf0f1;">'
            '<span>Итого:</span>'
            '<span style="color: #e74c3c;">{}</span>'
            '</div>'
            '</div>',
            format_price(items_cost),
            discount_html,
            format_price(delivery_cost),
            format_price(postcard_cost),
            postcard_detail,
            format_price(total)
        )

    cost_breakdown_display.short_description = "Детализация стоимости"

    def get_total_cost_display(self, obj):
        """Полная стоимость заказа"""
        total = obj.get_total_cost()
        items_cost = obj.get_items_cost()
        discount_amount = obj.get_discount_amount()
        postcard_cost = obj.postcard_final_price
        delivery_cost = obj.delivery_cost

        # Форматируем сумму без лишних нулей
        def format_price(price):
            formatted = f"{price:.2f}"
            return formatted.replace('.00', '')

        return format_html(
            '<div style="font-size: 1.2em; font-weight: bold; color: #e53935;">{} руб.</div>'
            '<div style="font-size: 0.85em; color: #666; margin-top: 5px;">'
            '{} = {} - {} + {} + {}'
            '</div>',
            format_price(total),
            format_price(total),
            format_price(items_cost),
            format_price(discount_amount),
            format_price(delivery_cost),
            format_price(postcard_cost)
        )

    get_total_cost_display.short_description = "Полная стоимость"

    def postcard_preview(self, obj):
        """Превью открытки из каталога"""
        if obj.postcard and obj.postcard.image:
            price_text = f"Цена: {obj.postcard_final_price} руб." if obj.postcard_final_price > 0 else "БЕСПЛАТНО"
            return format_html(
                '<div style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 8px;">'
                '<div style="font-weight: bold; color: {}; margin-bottom: 5px;">{}</div>'
                '<div style="color: #666; margin-bottom: 5px;">Название: {}</div>'
                '</div>'
                '<img src="{}" style="max-height: 300px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);" />',
                '#28a745' if obj.postcard_final_price > 0 else '#666',
                price_text,
                obj.postcard.title,
                obj.postcard.image.url
            )
        return "-"

    postcard_preview.short_description = "Превью (Каталог)"

    def custom_postcard_preview(self, obj):
        """Превью своей фото-открытки"""
        if obj.custom_postcard_image:
            price_info = ""
            if obj.postcard_final_price > 0:
                price_info = format_html(
                    '<div style="margin-bottom: 10px; padding: 10px; background: #e8f5e9; border-radius: 8px; border: 1px solid #c8e6c9;">'
                    '<div style="font-weight: bold; color: #2e7d32;">Цена: {} руб.</div>'
                    '<div style="color: #666; font-size: 0.9em;">'
                    '{}'
                    '</div>'
                    '</div>',
                    obj.postcard_final_price,
                    'Своё фото' + (f' + основа "{obj.postcard.title}"' if obj.postcard else '')
                )
            else:
                price_info = format_html(
                    '<div style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 8px;">'
                    '<div style="font-weight: bold; color: #666;">БЕСПЛАТНО</div>'
                    '<div style="color: #666; font-size: 0.9em;">'
                    '{}'
                    '</div>'
                    '</div>',
                    'Своё фото' + (f' + основа "{obj.postcard.title}"' if obj.postcard else '')
                )

            return format_html(
                '{}'
                '<div style="color: #9c27b0; font-weight: bold; margin-bottom: 10px;">'
                '📸 Загружено клиентом'
                '</div>'
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-height: 300px; border-radius: 8px; border: 2px solid #9c27b0;" />'
                '</a>',
                price_info,
                obj.custom_postcard_image.url,
                obj.custom_postcard_image.url
            )
        return "-"

    custom_postcard_preview.short_description = "Превью (Клиент)"

    # === VIEWS ДЛЯ КНОПОК ===
    def send_confirmation_email_view(self, request, object_id):
        """Отправка подтверждения заказа"""
        try:
            order = Order.objects.get(id=object_id)
            if not order.email or 'no-email' in order.email:
                self.message_user(request, f'Нет валидного email у заказа #{order.id}', messages.WARNING)
                return redirect(reverse('admin:orders_order_change', args=[object_id]))

            async_task('orders.utils.send_order_confirmation_email_task', order_id=order.id)
            self.message_user(request, f'Подтверждение заказа #{order.id} отправляется.', messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f'Ошибка: {str(e)}', messages.ERROR)

        return redirect(reverse('admin:orders_order_change', args=[object_id]))

    def send_status_email_view(self, request, object_id):
        """Отправка уведомления о статусе"""
        try:
            order = Order.objects.get(id=object_id)
            if not order.email or 'no-email' not in order.email:
                self.message_user(request, f'Нет валидного email у заказа #{order.id}', messages.WARNING)
                return redirect(reverse('admin:orders_order_change', args=[object_id]))

            async_task('orders.utils.send_status_update_email_task', order_id=order.id)
            self.message_user(request, f'Уведомление о статусе заказа #{order.id} отправляется.', messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f'Ошибка: {str(e)}', messages.ERROR)

        return redirect(reverse('admin:orders_order_change', args=[object_id]))

    def notify_customer_full(self, request, object_id):
        """Старый метод (для совместимости)"""
        async_task('orders.utils.send_order_confirmation_email_task', order_id=object_id)
        self.message_user(request, "Письмо-подтверждение отправляется клиенту.", messages.SUCCESS)
        return redirect(reverse('admin:orders_order_change', args=[object_id]))

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, OrderItem) and instance.product and (instance.price is None or instance.price == 0):
                instance.price = instance.product.price
            instance.save()
        formset.save_m2m()

    def has_add_permission(self, request):
        return False

    # === ACTIONS ===
    actions = ['mark_as_paid', 'mark_as_delivered', 'mark_as_shipped', 'mark_as_cancelled',
               'send_notification_to_selected', 'send_confirmation_bulk', 'send_status_bulk']

    @admin.action(description='Отметить как Оплаченные')
    def mark_as_paid(self, request, queryset):
        queryset.update(paid=True)
        self.message_user(request, "Заказы отмечены как оплаченные.")

    @admin.action(description='Отметить как Доставленные')
    def mark_as_delivered(self, request, queryset):
        queryset.update(status='delivered')
        self.message_user(request, "Статус обновлен на 'Доставлен'.")

    @admin.action(description='Отметить как Отправленные')
    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
        self.message_user(request, "Статус обновлен на 'Отправлен'.")

    @admin.action(description='Отметить как Отмененные')
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, "Статус обновлен на 'Отменен'.")

    @admin.action(description='Отправить уведомление о статусе')
    def send_notification_to_selected(self, request, queryset):
        for order in queryset:
            async_task('orders.utils.send_status_update_email_task', order_id=order.id)
        self.message_user(request, "Задачи на отправку уведомлений созданы.")

    @admin.action(description='📧 Отправить подтверждение заказа')
    def send_confirmation_bulk(self, request, queryset):
        count = 0
        for order in queryset:
            if order.email and 'no-email' not in order.email:
                async_task('orders.utils.send_order_confirmation_email_task', order_id=order.id)
                count += 1
        self.message_user(request, f"Задачи на отправку подтверждений созданы для {count} заказов", messages.SUCCESS)

    send_confirmation_bulk.short_description = "📧 Отправить подтверждение (повторно)"

    @admin.action(description='🔄 Отправить уведомление о статусе')
    def send_status_bulk(self, request, queryset):
        count = 0
        for order in queryset:
            if order.email and 'no-email' not in order.email:
                async_task('orders.utils.send_status_update_email_task', order_id=order.id)
                count += 1
        self.message_user(request, f"Задачи на отправку уведомлений о статусе созданы для {count} заказов",
                          messages.SUCCESS)

    send_status_bulk.short_description = "🔄 Уведомить о статусе (повторно)"