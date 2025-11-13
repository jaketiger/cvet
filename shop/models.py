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

    # --- НОВОЕ ПОЛЕ ДЛЯ СОРТИРОВКИ ---
    order = models.PositiveIntegerField("Порядок", default=0, help_text="Чем меньше число, тем левее категория в меню")

    class Meta:
        # --- ИЗМЕНЕНИЕ: СОРТИРУЕМ ПО НОВОМУ ПОЛЮ ---
        ordering = ['order']
        indexes = [models.Index(fields=['name']),]
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
    category = models.ManyToManyField(Category, related_name='products', blank=True, verbose_name="Категории")
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
    is_featured = models.BooleanField(default=False, verbose_name="Показывать на главной")
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

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField("Телефон", max_length=20, blank=True)
    address = models.CharField("Адрес", max_length=250, blank=True)
    postal_code = models.CharField("Индекс", max_length=20, blank=True)
    city = models.CharField("Город", max_length=100, blank=True)

    def __str__(self):
        return f'Профиль пользователя {self.user.username}'


class SiteSettings(SingletonModel):
    shop_name = models.CharField("Название магазина", max_length=100, default="MegaCvet")
    delivery_cost = models.DecimalField("Стоимость доставки по городу", max_digits=10, decimal_places=2, default=350.00)
    pickup_address = models.TextField("Адрес для самовывоза", blank=True)
    working_hours = models.CharField("График работы", max_length=200, blank=True)
    contact_phone = models.CharField("Контактный телефон", max_length=50, blank=True)
    banner_image = models.ImageField("Изображение для баннера", upload_to='banners/', blank=True, null=True)
    banner_title = models.CharField("Заголовок на баннере", max_length=200, blank=True)
    banner_subtitle = models.CharField("Подзаголовок на баннере", max_length=300, blank=True)
    banner_link = models.URLField("Ссылка для кнопки на баннере (URL)", blank=True)
    admin_notification_emails = models.TextField(
        "Email для уведомлений о заказах", blank=True,
        help_text="Введите email-адреса через запятую, на которые будут приходить уведомления о новых заказах."
    )
    background_image = models.ImageField(
        "Фоновое изображение сайта",
        upload_to='backgrounds/',
        blank=True, null=True,
        help_text="Если не выбрано, будет использоваться фон по умолчанию из static/shop/img/background.jpg"
    )

    class Meta:
        verbose_name = "Настройки сайта"

    def __str__(self):
        return "Настройки сайта"


class FooterPage(models.Model):
    title = models.CharField("Название ссылки", max_length=50)
    page_title = models.CharField("Заголовок на странице", max_length=200, blank=True,
                                  help_text="Если оставить пустым, будет использовано название ссылки")
    slug = models.SlugField("URL-адрес", unique=True,
                            help_text="Только английские буквы, цифры и дефисы. Например, 'about-us'")
    content = models.TextField("Содержимое страницы", blank=True)
    order = models.PositiveIntegerField("Порядок", default=0, help_text="Чем меньше число, тем левее ссылка")

    class Meta:
        ordering = ['order']
        verbose_name = "Страница в футере"
        verbose_name_plural = "Страницы в футере"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('shop:footer_page_detail', args=[self.slug])

    def get_page_title(self):
        return self.page_title or self.title


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()