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
    extra = 0  # Чтобы не было пустых строк для добавления


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'type_display',
        'first_name', 'last_name',
        'recipient_display',
        'delivery_date_fmt',
        'delivery_time',
        'status', 'paid',
        'delivery_option',
        'postcard_status_column',
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
        'get_items_cost_display', 'get_total_cost_display',
        'postcard_preview', 'custom_postcard_preview', 'is_one_click'
    )

    # === ВКЛЮЧАЕМ КНОПКИ СОХРАНЕНИЯ НАВЕРХУ ===
    save_on_top = True

    # Шаблон списка (для кнопки автосохранения)
    change_list_template = "admin/orders/order/change_list.html"

    # Шаблон редактирования удален, так как используем стандартный + save_on_top
    # change_form_template = "admin/orders/order/change_form.html"

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
        ('Стоимость и технические даты', {
            'fields': ('get_items_cost_display', 'get_total_cost_display', 'created', 'updated')
        }),
    )

    # === ПОДКЛЮЧЕНИЕ СТИЛЕЙ И СКРИПТОВ (ИСПРАВЛЕНО) ===
    @property
    def media(self):
        media = super().media
        # Используем списки для файлов, чтобы избежать ошибок
        extra_css = {'all': ['shop/css/admin_custom_buttons.css']}
        extra_js = []

        try:
            if SiteSettings.get_solo().enable_admin_autosave:
                extra_js.append('shop/js/admin_auto_save.js')
        except:
            pass

        # Безопасное сложение медиа-объектов
        return media + forms.Media(css=extra_css, js=extra_js)

    # === URLS (ИСПРАВЛЕН ПОРЯДОК) ===
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

            # 4. Ваша старая кнопка notify (оставляем для совместимости)
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
        # Возвращаемся на ту же страницу
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

    # === КОНТЕКСТ ДЛЯ СПИСКА ЗАКАЗОВ (ЧТОБЫ КНОПКА ЗНАЛА СТАТУС) ===
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            extra_context['autosave_enabled'] = SiteSettings.get_solo().enable_admin_autosave
        except:
            extra_context['autosave_enabled'] = False
        return super().changelist_view(request, extra_context=extra_context)

    # === МЕТОД ОТОБРАЖЕНИЯ ТИПА ЗАКАЗА ===
    def type_display(self, obj):
        if obj.is_one_click:
            return format_html(
                '<span style="color: orange; font-weight: bold; font-size: 1.2em;" title="Быстрый заказ">⚡ 1-Click</span>')
        return format_html('<span style="color: #666;" title="Обычный заказ">🛒 Корзина</span>')

    type_display.short_description = "Тип"

    # =====================================

    def delivery_date_fmt(self, obj):
        if obj.delivery_date:
            return obj.delivery_date.strftime('%d.%m.%Y')
        return "-"

    delivery_date_fmt.short_description = "Дата доставки"

    def recipient_display(self, obj):
        if obj.recipient_name:
            return f"🎁 {obj.recipient_name}"
        return "👤 Заказчик"

    recipient_display.short_description = "Получатель"

    def postcard_status_column(self, obj):
        if obj.custom_postcard_image:
            return format_html('<span style="color: purple; font-weight: bold;">📸 Своё фото</span>')
        elif obj.postcard:
            if obj.postcard.price > 0:
                return format_html('<span style="color: green;">💰 {} ({}р)</span>', obj.postcard.title,
                                   obj.postcard.price)
            else:
                return format_html('<span style="color: #666;">🎁 {} (Беспл.)</span>', obj.postcard.title)
        return "-"

    postcard_status_column.short_description = "Открытка"

    def postcard_preview(self, obj):
        if obj.postcard and obj.postcard.image:
            price_tag = f"Цена: {obj.postcard.price} руб." if obj.postcard.price > 0 else "БЕСПЛАТНО"
            return format_html(
                '<div style="margin-bottom: 5px; font-weight: bold;">{}</div>'
                '<img src="{}" style="max-height: 300px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);" />',
                price_tag, obj.postcard.image.url
            )
        return "-"

    postcard_preview.short_description = "Превью (Каталог)"

    def custom_postcard_preview(self, obj):
        if obj.custom_postcard_image:
            return format_html(
                '<div style="margin-bottom: 5px; font-weight: bold; color: purple;">Загружено клиентом</div>'
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 300px; border-radius: 8px;" /></a>',
                obj.custom_postcard_image.url, obj.custom_postcard_image.url
            )
        return "-"

    custom_postcard_preview.short_description = "Превью (Клиент)"

    def get_total_cost_display(self, obj):
        return f"{obj.get_total_cost()} руб."

    get_total_cost_display.short_description = "Полная стоимость"

    def get_items_cost_display(self, obj):
        return f"{obj.get_items_cost()} руб."

    get_items_cost_display.short_description = "Стоимость товаров"

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

    # === НОВЫЕ ДЕЙСТВИЯ (BULK) ===
    @admin.action(description='📧 Отправить подтверждение заказа')
    def send_confirmation_bulk(self, request, queryset):
        count = 0
        for order in queryset:
            if order.email and 'no-email' not in order.email:
                async_task('orders.utils.send_order_confirmation_email_task', order_id=order.id)
                count += 1
        self.message_user(
            request,
            f"Задачи на отправку подтверждений созданы для {count} заказов",
            messages.SUCCESS
        )

    send_confirmation_bulk.short_description = "📧 Отправить подтверждение (повторно)"

    @admin.action(description='🔄 Отправить уведомление о статусе')
    def send_status_bulk(self, request, queryset):
        count = 0
        for order in queryset:
            if order.email and 'no-email' not in order.email:
                async_task('orders.utils.send_status_update_email_task', order_id=order.id)
                count += 1
        self.message_user(
            request,
            f"Задачи на отправку уведомлений о статусе созданы для {count} заказов",
            messages.SUCCESS
        )

    send_status_bulk.short_description = "🔄 Уведомить о статусе (повторно)"

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
            if not order.email or 'no-email' in order.email:
                self.message_user(request, f'Нет валидного email у заказа #{order.id}', messages.WARNING)
                return redirect(reverse('admin:orders_order_change', args=[object_id]))

            async_task('orders.utils.send_status_update_email_task', order_id=order.id)
            self.message_user(request, f'Уведомление о статусе заказа #{order.id} отправляется.', messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f'Ошибка: {str(e)}', messages.ERROR)

        return redirect(reverse('admin:orders_order_change', args=[object_id]))

    def notify_customer_full(self, request, object_id):
        """Ваш старый метод (для совместимости)"""
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