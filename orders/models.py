# orders/models.py

from django.db import models
from shop.models import Product, Postcard, SiteSettings  # <--- Импорт SiteSettings
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models import Max  # <--- Импорт Max


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

    # Выбор времени (Интервалы)
    DELIVERY_TIME_CHOICES = [
        ('09-12', '09:00 - 12:00'),
        ('12-15', '12:00 - 15:00'),
        ('15-18', '15:00 - 18:00'),
        ('18-21', '18:00 - 21:00'),
        ('any', 'В любое время'),
    ]
    delivery_date = models.DateField("Дата доставки", null=True, blank=True)
    delivery_time = models.CharField("Время доставки", max_length=20, choices=DELIVERY_TIME_CHOICES, default='any')

    DELIVERY_CHOICES = [('delivery', 'Доставка'), ('pickup', 'Самовывоз')]
    delivery_option = models.CharField("Способ получения", max_length=10, choices=DELIVERY_CHOICES, default='delivery')
    delivery_cost = models.DecimalField("Стоимость доставки", max_digits=10, decimal_places=2, default=0.00)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders',
                             verbose_name="Пользователь")

    first_name = models.CharField(max_length=50, verbose_name="Имя")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    email = models.EmailField(verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Телефон")

    address = models.CharField(max_length=250, verbose_name="Адрес доставки")
    city = models.CharField(max_length=100, verbose_name="Город")
    postal_code = models.CharField(max_length=20, verbose_name="Почтовый индекс", blank=True)

    created = models.DateTimeField(auto_now_add=True, verbose_name="Создан")
    updated = models.DateTimeField(auto_now=True, verbose_name="Обновлен")
    paid = models.BooleanField(default=False, verbose_name="Оплачен")

    recipient_name = models.CharField("Имя получателя", max_length=100, blank=True)
    recipient_phone = models.CharField("Телефон получателя", max_length=20, blank=True)

    # Поля для открытки
    postcard = models.ForeignKey(Postcard, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='orders_with_card', verbose_name="Открытка")
    postcard_text = models.TextField("Текст открытки", blank=True)
    custom_postcard_image = models.ImageField("Своё фото открытки", upload_to='orders/postcards/', blank=True)

    # === ЛОГИКА ГЕНЕРАЦИИ НОМЕРА ЗАКАЗА (ID) ===
    def save(self, *args, **kwargs):
        if not self.id:
            # 1. Получаем стартовое число из настроек
            try:
                start_num = SiteSettings.get_solo().order_start_number
            except:
                start_num = 1  # Если настроек нет

            # 2. Ищем максимальный существующий ID
            max_id_dict = Order.objects.aggregate(Max('id'))
            max_id = max_id_dict['id__max'] or 0

            # 3. Присваиваем новый ID
            # Берем максимум из (существующий + 1) и (число из настроек)
            # Это позволяет "перепрыгнуть" вперед, но не дает перезаписать существующие
            self.id = max(max_id + 1, start_num)

        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created']
        indexes = [models.Index(fields=['-created']), ]
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'Заказ #{self.id}'

    @property
    def can_be_cancelled(self):
        return self.status in ['created', 'processing']

    def get_items_cost(self):
        return sum(item.get_cost() for item in self.items.all())

    def get_total_cost(self):
        # Базовая стоимость (товары + доставка)
        total = self.get_items_cost() + self.delivery_cost
        # Если выбрана платная открытка
        if self.postcard and self.postcard.price > 0:
            total += self.postcard.price
        return total


class OrderItem(models.Model):
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
        if self.price is None or self.quantity is None:
            return Decimal('0.00')
        return self.price * self.quantity