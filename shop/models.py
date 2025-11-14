# shop/models.py

from django.db import models
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill
from django.urls import reverse
from solo.models import SingletonModel
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator, MaxValueValidator

GLOBAL_FONT_FAMILY_CHOICES = [('roboto', 'Стандартный (Roboto)'), ('montserrat', 'Современный (Montserrat)'),
                              ('open-sans', 'Дружелюбный (Open Sans)'), ('lora', 'Элегантный (Lora)'),
                              ('merriweather', 'Классический (Merriweather)'),
                              ('playfair-display', 'Журнальный (Playfair Display)'),
                              ('lobster', 'Декоративный (Lobster)'), ('pacifico', 'Мягкий (Pacifico)'), ]


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название категории");
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL");
    order = models.PositiveIntegerField("Порядок", default=0, help_text="Чем меньше число, тем левее категория в меню")

    class Meta: ordering = ['order']; indexes = [
        models.Index(fields=['name']), ]; verbose_name = 'Категория'; verbose_name_plural = 'Категории'

    def __str__(self): return self.name

    def get_absolute_url(self): return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
    category = models.ManyToManyField(Category, related_name='products', blank=True, verbose_name="Категории");
    name = models.CharField(max_length=200, verbose_name="Название товара");
    slug = models.SlugField(max_length=200, verbose_name="URL");
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, verbose_name="Основное изображение");
    image_thumbnail = ImageSpecField(source='image', processors=[ResizeToFill(300, 250)], format='JPEG',
                                     options={'quality': 80});
    description_right_title = models.CharField("Уникальный заголовок блока справа", max_length=100, blank=True,
                                               help_text="Если оставить пустым, будет использован заголовок из Настроек сайта.");
    description_right = models.TextField("Текстовый блок (справа от фото)", blank=True);
    description_bottom_title = models.CharField("Уникальный заголовок блока внизу", max_length=100, blank=True,
                                                help_text="Если оставить пустым, будет использован заголовок из Настроек сайта.");
    description_bottom = models.TextField("Текстовый блок (под фото)", blank=True);
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена");
    stock = models.PositiveIntegerField(verbose_name="Остаток на складе");
    available = models.BooleanField(default=True, verbose_name="Доступен для заказа");
    is_featured = models.BooleanField(default=False, verbose_name="Показывать на главной");
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания");
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta: ordering = ['name']; indexes = [models.Index(fields=['id', 'slug']), models.Index(fields=['name']),
                                                models.Index(fields=[
                                                    '-created']), ]; verbose_name = 'Товар'; verbose_name_plural = 'Товары'

    def __str__(self): return self.name

    def get_absolute_url(self): return reverse('shop:product_detail', args=[self.id, self.slug])


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Товар');
    image = models.ImageField(upload_to='products/gallery/%Y/%m/%d', verbose_name='Изображение');
    image_thumbnail = ImageSpecField(source='image', processors=[ResizeToFill(100, 100)], format='JPEG',
                                     options={'quality': 70});
    alt_text = models.CharField(max_length=255, blank=True, verbose_name='Альтернативный текст (для SEO)')

    class Meta: verbose_name = 'Изображение товара'; verbose_name_plural = 'Изображения товаров'; ordering = ['id']

    def __str__(self): return f"Изображение для {self.product.name}"


class Banner(models.Model):
    CONTENT_POSITION_CHOICES = [('center-center', 'По центру'), ('bottom-left', 'Внизу слева'),
                                ('bottom-right', 'Внизу справа'), ('top-left', 'Вверху слева'),
                                ('top-right', 'Вверху справа')]
    image = models.ImageField("Изображение (1600x600)", upload_to='banners/');
    title = models.CharField("Заголовок (необязательно)", max_length=200, blank=True);
    subtitle = models.CharField("Подзаголовок (необязательно)", max_length=300, blank=True)
    link = models.URLField("Ссылка (URL, необязательно)", blank=True);
    button_text = models.CharField("Текст на кнопке (необязательно)", max_length=50, blank=True,
                                   help_text="Если пусто, весь баннер будет ссылкой.")
    content_position = models.CharField("Расположение текста", max_length=20, choices=CONTENT_POSITION_CHOICES,
                                        default='center-center')
    background_opacity = models.FloatField("Прозрачность фона текста (%)", default=45,
                                           validators=[MinValueValidator(0), MaxValueValidator(100)],
                                           help_text="От 0 (полностью прозрачный) до 100 (непрозрачный).")
    font_color = models.CharField("Цвет шрифта", max_length=7, default='#FFFFFF',
                                  help_text="В формате HEX, например, #FFFFFF для белого.")
    font_family = models.CharField("Стиль шрифта", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, default='roboto')
    is_active = models.BooleanField("Активен", default=True, help_text="Только активные баннеры будут показаны.");
    order = models.PositiveIntegerField("Порядок", default=0, help_text="Чем меньше число, тем раньше.")

    @property
    def background_opacity_css(self): return self.background_opacity / 100

    class Meta: verbose_name = "Баннер"; verbose_name_plural = "Баннеры"; ordering = ['order']

    def __str__(self): return self.title or f"Баннер #{self.id}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile');
    phone = models.CharField("Телефон", max_length=20, blank=True);
    address = models.CharField("Адрес", max_length=250, blank=True);
    postal_code = models.CharField("Индекс", max_length=20, blank=True);
    city = models.CharField("Город", max_length=100, blank=True)

    def __str__(self): return f'Профиль пользователя {self.user.username}'


class SiteSettings(SingletonModel):
    # --- Основные ---
    shop_name = models.CharField("Название магазина", max_length=100, default="MegaCvet");
    contact_phone = models.CharField("Контактный телефон", max_length=50, blank=True);
    admin_notification_emails = models.TextField("Email для уведомлений", blank=True);
    background_image = models.ImageField("Фоновое изображение", upload_to='backgrounds/', blank=True, null=True)
    delivery_cost = models.DecimalField("Стоимость доставки", max_digits=10, decimal_places=2, default=300.00,
                                        help_text="Стоимость доставки будет добавлена к общей сумме заказа.")

    # --- Глобальное оформление ---
    main_text_color = models.CharField("Основной цвет текста", max_length=7, default='#333333');
    accent_color = models.CharField("Акцентный цвет (ссылки, кнопки)", max_length=7, default='#e53935');
    body_font_family = models.CharField("Шрифт для основного текста", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES,
                                        default='roboto');
    heading_font_family = models.CharField("Шрифт для заголовков", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES,
                                           default='montserrat');
    base_font_size = models.PositiveIntegerField("Базовый размер шрифта (px)", default=16)

    # --- Стилизация логотипа ---
    logo_color = models.CharField("Цвет", max_length=7, blank=True, help_text="Пусто = глобальный цвет");
    logo_font_size = models.PositiveIntegerField("Размер (px)", blank=True, null=True,
                                                 help_text="Пусто = по умолчанию");
    logo_font_family = models.CharField("Стиль шрифта названия", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES,
                                        blank=True)

    # --- Тонкие настройки ---
    category_nav_font_family = models.CharField("Стиль шрифта", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES,
                                                blank=True)
    category_nav_font_size = models.PositiveIntegerField("Размер (px)", blank=True, null=True)
    category_nav_font_color = models.CharField("Цвет текста", max_length=7, blank=True)
    category_nav_hover_color = models.CharField("Цвет при наведении", max_length=7, blank=True)
    product_card_title_font_family = models.CharField("Шрифт названия", max_length=50,
                                                      choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True)
    product_card_title_font_size = models.PositiveIntegerField("Размер названия (px)", blank=True, null=True)
    product_card_title_color = models.CharField("Цвет названия", max_length=7, blank=True)
    product_card_price_color = models.CharField("Цвет цены", max_length=7, blank=True)
    footer_font_size = models.PositiveIntegerField("Размер шрифта (px)", blank=True, null=True)
    footer_font_color = models.CharField("Цвет текста", max_length=7, blank=True)

    # --- Стилизация кнопок ---
    button_bg_color = models.CharField("Цвет фона", max_length=7, blank=True, help_text="Пусто = акцентный цвет")
    button_text_color = models.CharField("Цвет текста", max_length=7, blank=True, help_text="Пусто = белый")
    button_hover_bg_color = models.CharField("Цвет фона при наведении", max_length=7, blank=True,
                                             help_text="Пусто = темно-серый (#333)")
    button_border_radius = models.PositiveIntegerField("Скругление углов (px)", blank=True, null=True,
                                                       help_text="Пусто = 5px")
    button_font_family = models.CharField("Стиль шрифта", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True,
                                          help_text="Пусто = шрифт основного текста")

    # --- ДОБАВЛЕНО: Поля для кнопки "В корзину" ---
    add_to_cart_bg_color = models.CharField("Цвет фона кнопки 'В корзину'", max_length=7, blank=True,
                                            help_text="Если пусто, используется основной цвет кнопок.")
    add_to_cart_text_color = models.CharField("Цвет текста кнопки 'В корзину'", max_length=7, blank=True,
                                              help_text="Если пусто, используется основной цвет текста кнопок.")
    add_to_cart_hover_bg_color = models.CharField("Цвет фона 'В корзину' при наведении", max_length=7, blank=True,
                                                  help_text="Если пусто, используется основной цвет кнопок при наведении.")

    # --- Настройки слайдера ---
    SLIDER_EFFECT_CHOICES = [('slide', 'Пролистывание'), ('fade', 'Наплыв'), ('cube', '3D Куб'),
                             ('flip', '3D Переворот')];
    slider_duration = models.PositiveIntegerField("Пауза (сек)", default=5);
    slider_effect = models.CharField("Эффект", max_length=10, choices=SLIDER_EFFECT_CHOICES, default='slide')

    # --- Остальное ---
    product_description_right_title = models.CharField("Заголовок блока справа (по умолч.)", max_length=100,
                                                       default="Описание");
    product_description_bottom_title = models.CharField("Заголовок блока внизу (по умолч.)", max_length=100,
                                                        default="Состав")

    class Meta: verbose_name = "Настройки сайта"

    def __str__(self): return "Настройки сайта"


class FooterPage(models.Model):
    title = models.CharField("Название ссылки", max_length=50);
    page_title = models.CharField("Заголовок на странице", max_length=200, blank=True);
    slug = models.SlugField("URL-адрес", unique=True);
    content = models.TextField("Содержимое страницы", blank=True);
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta: ordering = ['order']; verbose_name = "Страница в футере"; verbose_name_plural = "Страницы в футере"

    def __str__(self): return self.title

    def get_absolute_url(self): return reverse('shop:footer_page_detail', args=[self.slug])

    def get_page_title(self): return self.page_title or self.title


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created: Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'): instance.profile.save()