# orders/admin.py

from django.contrib import admin, messages
from django import forms
from .models import Order, OrderItem
from django.urls import reverse, path
from django.shortcuts import redirect
from django_q.tasks import async_task  # <-- ИЗМЕНЕНИЕ: Импортируем async_task


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
        'id', 'first_name', 'last_name', 'email', 'status', 'paid',
        'delivery_option', 'get_total_cost_display', 'created'
    )
    list_filter = ('status', 'paid', 'created', 'updated', 'delivery_option')
    search_fields = ('id', 'first_name', 'last_name', 'email', 'phone')

    # 2. Настройки страницы редактирования
    inlines = [OrderItemInline]
    readonly_fields = (
        'id', 'user', 'first_name', 'last_name', 'email', 'phone', 'address',
        'postal_code', 'city', 'created', 'updated', 'delivery_option',
        'delivery_cost', 'get_items_cost_display', 'get_total_cost_display'
    )
    fieldsets = (
        ('Основная информация', {'fields': ('user', 'status', 'paid')}),
        ('Данные клиента', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Доставка', {'fields': ('delivery_option', 'address', 'postal_code', 'city')}),
        ('Стоимость', {'fields': ('get_items_cost_display', 'delivery_cost', 'get_total_cost_display')}),
        ('Даты', {'fields': ('created', 'updated')}),
    )
    change_form_template = "admin/orders/order/change_form.html"

    # 3. Кастомные действия для массового обновления
    actions = ['mark_as_paid', 'mark_as_delivered', 'mark_as_shipped', 'mark_as_cancelled',
               'send_notification_to_selected']

    @admin.action(description='Отметить выбранные как Оплаченные')
    def mark_as_paid(self, request, queryset):
        updated_count = queryset.update(paid=True)
        self.message_user(request, f"{updated_count} заказ(ов) был(о) отмечен(о) как 'Оплачен'.")

    @admin.action(description='Отметить выбранные как Доставленные')
    def mark_as_delivered(self, request, queryset):
        updated_count = queryset.update(status='delivered')
        self.message_user(request, f"{updated_count} заказ(ов) был(о) отмечен(о) как 'Доставлен'.")

    @admin.action(description='Отметить выбранные как Отправленные')
    def mark_as_shipped(self, request, queryset):
        updated_count = queryset.update(status='shipped')
        self.message_user(request, f"{updated_count} заказ(ов) был(о) отмечен(о) как 'Отправлен'.")

    @admin.action(description='Отметить выбранные как Отмененные')
    def mark_as_cancelled(self, request, queryset):
        updated_count = queryset.update(status='cancelled')
        self.message_user(request, f"{updated_count} заказ(ов) был(о) отмечен(о) как 'Отменен'.")

    @admin.action(description='Отправить уведомление о статусе выбранным клиентам')
    def send_notification_to_selected(self, request, queryset):
        # --- ИЗМЕНЕНИЕ: Ставим задачи в очередь вместо прямого вызова ---
        for order in queryset:
            async_task('orders.utils.send_status_update_email_task', order_id=order.id)

        # Сообщаем пользователю, что задачи были поставлены в очередь
        self.message_user(request,
                          f"Задачи на отправку уведомлений для {queryset.count()} заказов были поставлены в очередь.")
        # -----------------------------------------------------------------

    # 4. Кастомные URL'ы и методы для кнопки
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/notify/', self.admin_site.admin_view(self.notify_customer_full),
                 name='order_notify_customer_full')
        ]
        return custom_urls + urls

    def notify_customer_full(self, request, object_id):
        order = self.get_object(request, object_id)
        if order:
            # --- ИЗМЕНЕНИЕ: Ставим задачу в очередь вместо прямого вызова ---
            async_task('orders.utils.send_order_confirmation_email_task', order_id=object_id)
            self.message_user(request, "Задача на отправку подтверждения заказа поставлена в очередь.",
                              messages.SUCCESS)
            # -----------------------------------------------------------------
        return redirect(reverse('admin:orders_order_change', args=[object_id]))

    # Метод для автозаполнения цены
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, OrderItem) and instance.product and (instance.price is None or instance.price == 0):
                instance.price = instance.product.price
            instance.save()
        formset.save_m2m()

    # 5. Вспомогательные методы
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items__product')

    def get_total_cost_display(self, obj):
        return f"{obj.get_total_cost()} руб."

    get_total_cost_display.short_description = "Полная стоимость"

    def get_items_cost_display(self, obj):
        return f"{obj.get_items_cost()} руб."

    get_items_cost_display.short_description = "Стоимость товаров"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False