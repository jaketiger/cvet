# orders/admin.py

from django.contrib import admin, messages
from django import forms
from .models import Order, OrderItem
from django.urls import reverse, path
from django.shortcuts import redirect
from django.utils.html import format_html
from django_q.tasks import async_task


class OrderItemForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Поле "Цена" в этой форме не является обязательным для заполнения
        self.fields['price'].required = False


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    form = OrderItemForm
    fields = ('product', 'price', 'quantity')
    autocomplete_fields = ['product']
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # 1. Настройки отображения списка
    list_display = (
        'id',
        'first_name', 'last_name',
        'recipient_display',        # <--- Кто получает
        'status', 'paid',
        'delivery_option',
        'postcard_status_column',   # <--- Статус открытки
        'get_total_cost_display',
        'created'
    )
    list_filter = ('status', 'paid', 'created', 'updated', 'delivery_option')
    search_fields = ('id', 'first_name', 'last_name', 'email', 'phone', 'recipient_name', 'recipient_phone')

    # 2. Настройки страницы редактирования
    inlines = [OrderItemInline]
    readonly_fields = (
        'id', 'user', 'created', 'updated',
        'get_items_cost_display', 'get_total_cost_display',
        'postcard_preview', 'custom_postcard_preview'
    )

    fieldsets = (
        ('Основная информация', {
            'fields': ('status', 'paid', 'delivery_option', 'delivery_cost')
        }),
        ('Заказчик', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        # --- БЛОК ПОЛУЧАТЕЛЯ ---
        ('Получатель (если отличается)', {
            'fields': ('recipient_name', 'recipient_phone'),
            'description': 'Заполняется только если клиент выбрал опцию "Другой человек".'
        }),
        # -----------------------
        ('Доставка', {
            'fields': ('address', 'postal_code', 'city')
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
        ('Стоимость и даты', {
            'fields': ('get_items_cost_display', 'get_total_cost_display', 'created', 'updated')
        }),
    )

    change_form_template = "admin/orders/order/change_form.html"

    # --- Методы для отображения ---

    # Отображение получателя в списке
    def recipient_display(self, obj):
        if obj.recipient_name:
            return f"🎁 {obj.recipient_name}"
        return "👤 Заказчик"
    recipient_display.short_description = "Получатель"

    # Статус открытки (иконки)
    def postcard_status_column(self, obj):
        if obj.custom_postcard_image:
            return format_html('<span style="color: purple; font-weight: bold;">📸 Своё фото</span>')
        elif obj.postcard:
            if obj.postcard.price > 0:
                return format_html('<span style="color: green;">💰 {} ({}р)</span>', obj.postcard.title, obj.postcard.price)
            else:
                return format_html('<span style="color: #666;">🎁 {} (Беспл.)</span>', obj.postcard.title)
        return "-"
    postcard_status_column.short_description = "Открытка"

    # Превью открытки из базы
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

    # Превью пользовательской открытки
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

    # --- Действия (Actions) ---

    actions = ['mark_as_paid', 'mark_as_delivered', 'mark_as_shipped', 'mark_as_cancelled',
               'send_notification_to_selected']

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

    # --- URLs и кнопки ---

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/notify/', self.admin_site.admin_view(self.notify_customer_full),
                 name='order_notify_customer_full')
        ]
        return custom_urls + urls

    def notify_customer_full(self, request, object_id):
        async_task('orders.utils.send_order_confirmation_email_task', order_id=object_id)
        self.message_user(request, "Письмо-подтверждение отправляется клиенту.", messages.SUCCESS)
        return redirect(reverse('admin:orders_order_change', args=[object_id]))

    # --- Вспомогательные методы ---

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, OrderItem) and instance.product and (instance.price is None or instance.price == 0):
                instance.price = instance.product.price
            instance.save()
        formset.save_m2m()

    def has_add_permission(self, request):
        return False