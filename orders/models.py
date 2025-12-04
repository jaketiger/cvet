# orders/models.py

from django.db import models
from shop.models import Product, Postcard, SiteSettings
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models import Max
from promo.models import PromoCode


class Order(models.Model):
    # Поля для промокодов
    promo_code = models.ForeignKey(PromoCode, related_name='orders', null=True, blank=True, on_delete=models.SET_NULL,
                                   verbose_name="Промокод")
    discount = models.IntegerField(default=0, verbose_name="Скидка %")

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

    delivery_time = models.CharField(
        "Время доставки",
        max_length=50,
        default='asap',
        help_text="Выбранный интервал или 'Как можно быстрее'"
    )
    delivery_date = models.DateField("Дата доставки", null=True, blank=True)

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

    # ИСПРАВЛЕНО: Добавлено поле для сохранения цены открытки
    postcard_final_price = models.DecimalField(
        "Финальная цена открытки",
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Цена открытки на момент оформления заказа"
    )

    postcard = models.ForeignKey(Postcard, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='orders_with_card', verbose_name="Открытка")
    postcard_text = models.TextField("Текст открытки", blank=True)
    custom_postcard_image = models.ImageField("Своё фото открытки", upload_to='orders/postcards/', blank=True)

    is_one_click = models.BooleanField("Заказ в 1 клик", default=False)

    def save(self, *args, **kwargs):
        # ИСПРАВЛЕНО: Всегда берем цену из связанной открытки если есть
        if self.postcard:
            # Берем цену ТОЛЬКО из объекта открытки
            self.postcard_final_price = self.postcard.price
        elif self.custom_postcard_image:
            # ИСПРАВЛЕНО: Для "Свое фото" берем цену из настроек сайта
            try:
                site_settings = SiteSettings.get_solo()
                self.postcard_final_price = site_settings.custom_postcard_price or Decimal('0.00')
            except:
                self.postcard_final_price = Decimal('0.00')
        else:
            # Если открытки нет, цена = 0
            self.postcard_final_price = Decimal('0.00')

        if not self.id:
            try:
                start_num = SiteSettings.get_solo().order_start_number
            except:
                start_num = 1

            max_id_dict = Order.objects.aggregate(Max('id'))
            max_id = max_id_dict['id__max'] or 0

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
        """ИСПРАВЛЕНО: Стоимость товаров с округлением"""
        total = sum(item.get_cost() for item in self.items.all())
        return total.quantize(Decimal('0.01'))

    def get_discount_amount(self):
        """ИСПРАВЛЕНО: Возвращает сумму скидки в рублях с округлением"""
        if self.discount > 0:
            discount = self.get_items_cost() * (Decimal(self.discount) / Decimal(100))
            return discount.quantize(Decimal('0.01'))
        return Decimal(0)

    def get_postcard_cost(self):
        """ИСПРАВЛЕНО: Возвращает стоимость открытки из сохраненного поля"""
        return self.postcard_final_price

    def get_total_cost(self):
        """ИСПРАВЛЕНО: Полная стоимость заказа с учетом открытки и округлением"""
        total_items = self.get_items_cost()

        # 1. Вычитаем скидку
        discount_amount = self.get_discount_amount()
        total = total_items - discount_amount

        # 2. Добавляем доставку
        total += self.delivery_cost

        # 3. Добавляем открытку
        total += self.get_postcard_cost()

        return total.quantize(Decimal('0.01'))

    def get_delivery_time_display(self):
        """Красивое отображение времени доставки"""
        if self.delivery_time == 'asap':
            return 'Как можно быстрее'
        return self.delivery_time

    def get_postcard_display(self):
        """Возвращает информацию для отображения открытки"""
        if self.custom_postcard_image:
            if self.postcard_final_price > 0:
                return f"Своё фото ({self.postcard_final_price} руб.)"
            else:
                return "Своё фото (Бесплатно)"
        elif self.postcard:
            if self.postcard_final_price > 0:
                return f"{self.postcard.title} ({self.postcard_final_price} руб.)"
            else:
                return f"{self.postcard.title} (Бесплатно)"
        return "Без открытки"

    def get_postcard_info(self):
        """Детальная информация об открытке для шаблонов"""
        if self.custom_postcard_image:
            return {
                'type': 'custom',
                'title': 'Свое фото',
                'price': self.postcard_final_price,
                'has_image': True,
                'has_base': bool(self.postcard),
                'base_title': self.postcard.title if self.postcard else None
            }
        elif self.postcard:
            return {
                'type': 'catalog',
                'title': self.postcard.title,
                'price': self.postcard_final_price,
                'has_image': bool(self.postcard.image)
            }
        return None


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
        return (self.price * self.quantity).quantize(Decimal('0.01'))