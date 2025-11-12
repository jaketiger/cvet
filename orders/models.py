# orders/models.py

from django.db import models
from shop.models import Product
from django.contrib.auth.models import User
from decimal import Decimal # <-- Добавляем импорт

class Order(models.Model):
    STATUS_CHOICES = [
        ('created', 'Оформлен'),
        ('processing', 'В обработке'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    ]
    status = models.CharField(
        "Статус заказа", max_length=20, choices=STATUS_CHOICES, default='created'
    )
    DELIVERY_CHOICES = [('delivery', 'Доставка'), ('pickup', 'Самовывоз')]
    delivery_option = models.CharField("Способ получения", max_length=10, choices=DELIVERY_CHOICES, default='delivery')
    delivery_cost = models.DecimalField("Стоимость доставки", max_digits=10, decimal_places=2, default=0.00)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Пользователь")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.CharField(max_length=250, verbose_name="Адрес доставки")
    postal_code = models.CharField(max_length=20, verbose_name="Почтовый индекс")
    city = models.CharField(max_length=100, verbose_name="Город")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    paid = models.BooleanField(default=False, verbose_name="Оплачен")

    class Meta:
        ordering = ['-created']
        indexes = [models.Index(fields=['-created']),]
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ #{self.id}'

    # --- НОВЫЙ МЕТОД ---
    def get_items_cost(self):
        """Возвращает стоимость всех товаров в заказе (БЕЗ доставки)."""
        return sum(item.get_cost() for item in self.items.all())

    # --- ОБНОВЛЕННЫЙ МЕТОД ---
    def get_total_cost(self):
        """Возвращает полную стоимость заказа (товары + доставка)."""
        return self.get_items_cost() + self.delivery_cost


class OrderItem(models.Model):
    # ... (этот класс остается без изменений) ...
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE, verbose_name="Заказ")
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE, verbose_name="Товар")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")

    class Meta:
        verbose_name = 'Товар в заказе'
        verbose_name_plural = 'Товары в заказе'

    def __str__(self):
        return str(self.id)

    def get_cost(self):
        """
        Надежный метод расчета стоимости.
        Если цена или количество отсутствуют, возвращает 0.
        """
        if self.price is None or self.quantity is None:
            return Decimal('0.00')
        return self.price * self.quantity