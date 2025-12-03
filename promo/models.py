# promo/models.py

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class PromoCode(models.Model):
    code = models.CharField("Код купона", max_length=50, unique=True)
    valid_from = models.DateTimeField("Действует с")
    valid_to = models.DateTimeField("Действует по")
    discount = models.IntegerField(
        "Скидка (%)",
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Процент скидки от 0 до 100"
    )
    active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['-valid_to']

    def __str__(self):
        return self.code