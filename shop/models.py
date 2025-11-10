# shop/models.py

from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.urls import reverse
from solo.models import SingletonModel

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название категории")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL")

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['name']),]
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE, verbose_name="Категория")
    name = models.CharField(max_length=200, verbose_name="Название товара")
    slug = models.SlugField(max_length=200, verbose_name="URL")
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, verbose_name="Изображение")
    image_thumbnail = ImageSpecField(source='image',
                                     processors=[ResizeToFill(300, 250)],
                                     format='JPEG',
                                     options={'quality': 80})

    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")

    stock = models.PositiveIntegerField(verbose_name="Остаток на складе")
    available = models.BooleanField(default=True, verbose_name="Доступен для заказа")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['id', 'slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created']),
        ]
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name

    # --- ВОТ ВАЖНОЕ ИЗМЕНЕНИЕ ---
    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])


# --- НОВАЯ МОДЕЛЬ ДЛЯ НАСТРОЕК САЙТА ---
class SiteSettings(SingletonModel):
    delivery_cost = models.DecimalField(
        "Стоимость доставки по городу",
        max_digits=10, decimal_places=2, default=500.00
    )
    pickup_address = models.TextField("Адрес для самовывоза", blank=True)
    working_hours = models.CharField("График работы", max_length=200, blank=True)
    contact_phone = models.CharField("Контактный телефон", max_length=50, blank=True)

    class Meta:
        verbose_name = "Настройки сайта"

    def __str__(self):
        return "Настройки сайта"



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField("Телефон", max_length=20, blank=True)
    address = models.CharField("Адрес", max_length=250, blank=True)
    postal_code = models.CharField("Индекс", max_length=20, blank=True)
    city = models.CharField("Город", max_length=100, blank=True)

    def __str__(self):
        return f'Профиль пользователя {self.user.username}'

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

