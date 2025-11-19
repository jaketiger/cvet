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

GLOBAL_FONT_FAMILY_CHOICES = [
    ('roboto', 'Стандартный (Roboto)'),
    ('montserrat', 'Современный (Montserrat)'),
    ('open-sans', 'Дружелюбный (Open Sans)'),
    ('lora', 'Элегантный (Lora)'),
    ('merriweather', 'Классический (Merriweather)'),
    ('playfair-display', 'Журнальный (Playfair Display)'),
    ('lobster', 'Декоративный (Lobster)'),
    ('pacifico', 'Мягкий (Pacifico)'),
]

FONT_STYLE_CHOICES = [
    ('normal', 'Обычный'),
    ('bold', 'Жирный'),
    ('italic', 'Курсив'),
]

MENU_VIEW_MODE_CHOICES = [
    ('text', 'В виде текста'),
    ('buttons', 'В виде кнопок'),
]


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name="Название категории")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL")
    order = models.PositiveIntegerField("Порядок", default=0, help_text="Чем меньше число, тем левее категория в меню")

    class Meta:
        ordering = ['order']
        indexes = [models.Index(fields=['name']), ]
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self): return self.name

    def get_absolute_url(self): return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
    category = models.ManyToManyField(Category, related_name='products', blank=True, verbose_name="Категории")
    name = models.CharField(max_length=200, verbose_name="Название товара")
    slug = models.SlugField(max_length=200, verbose_name="URL")
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, verbose_name="Основное изображение")
    image_thumbnail = ImageSpecField(source='image', processors=[ResizeToFill(300, 250)], format='JPEG',
                                     options={'quality': 80})
    composition_title = models.CharField("Заголовок для 'Состава'", max_length=100, blank=True,
                                         help_text="Если пусто, будет использован заголовок из Настроек сайта.")
    composition = models.TextField("Состав (блок под фото)", blank=True)
    description_title = models.CharField("Заголовок для 'Описания'", max_length=100, blank=True,
                                         help_text="Если пусто, будет использован заголовок из Настроек сайта.")
    description = models.TextField("Описание (блок справа от фото)", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    stock = models.PositiveIntegerField(verbose_name="Остаток на складе")
    available = models.BooleanField(default=True, verbose_name="Доступен для заказа")
    is_featured = models.BooleanField(default=False, verbose_name="Показывать на главной")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['id', 'slug']), models.Index(fields=['name']),
                   models.Index(fields=['-created'])]
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self): return self.name

    def get_absolute_url(self): return reverse('shop:product_detail', args=[self.id, self.slug])


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Товар')
    image = models.ImageField(upload_to='products/gallery/%Y/%m/%d', verbose_name='Изображение')
    image_thumbnail = ImageSpecField(source='image', processors=[ResizeToFill(100, 100)], format='JPEG',
                                     options={'quality': 70})
    alt_text = models.CharField(max_length=255, blank=True, verbose_name='Альтернативный текст (для SEO)')

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['id']

    def __str__(self): return f"Изображение для {self.product.name}"


class Banner(models.Model):
    CONTENT_POSITION_CHOICES = [('center-center', 'По центру'), ('bottom-left', 'Внизу слева'),
                                ('bottom-right', 'Внизу справа'), ('top-left', 'Вверху слева'),
                                ('top-right', 'Вверху справа')]
    image = models.ImageField("Изображение (1600x600)", upload_to='banners/')
    title = models.CharField("Заголовок (необязательно)", max_length=200, blank=True)
    subtitle = models.CharField("Подзаголовок (необязательно)", max_length=300, blank=True)
    link = models.URLField("Ссылка (URL, необязательно)", blank=True)
    button_text = models.CharField("Текст на кнопке (необязательно)", max_length=50, blank=True,
                                   help_text="Если пусто, весь баннер будет ссылкой.")
    content_position = models.CharField("Расположение текста", max_length=20, choices=CONTENT_POSITION_CHOICES,
                                        default='center-center')
    background_opacity = models.FloatField("Прозрачность фона текста", default=45,
                                           validators=[MinValueValidator(0), MaxValueValidator(100)])
    font_color = models.CharField("Цвет шрифта", max_length=7, blank=True,
                                  help_text="Сброс к значению по умолчанию: очистите поле (нажмите ×)")
    font_family = models.CharField("Стиль шрифта", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, default='roboto')
    is_active = models.BooleanField("Активен", default=True, help_text="Только активные баннеры будут показаны.")
    order = models.PositiveIntegerField("Порядок", default=0, help_text="Чем меньше число, тем раньше.")

    @property
    def background_opacity_css(self): return self.background_opacity / 100

    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"
        ordering = ['order']

    def __str__(self): return self.title or f"Баннер #{self.id}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField("Телефон", max_length=20, blank=True)
    address = models.CharField("Адрес", max_length=250, blank=True)
    postal_code = models.CharField("Индекс", max_length=20, blank=True)
    city = models.CharField("Город", max_length=100, blank=True)

    def __str__(self): return f'Профиль пользователя {self.user.username}'


class SiteSettings(SingletonModel):
    NAV_STYLE_CHOICES = [('underline', 'Анимация подчеркивания'), ('highlight', 'Фоновая подсветка'),
                         ('lift', 'Эффект приподнимания'), ('shadow', 'Сдвиг с тенью (3D)'),
                         ('wave', '"Жидкая" волна'), ]
    ICON_ANIMATION_CHOICES = [
        ('scale', 'Увеличение (стандарт)'),
        ('rotate', 'Вращение'),
        ('bounce', 'Подпрыгивание'),
    ]

    MOBILE_HEADER_CHOICES = [
        ('partial', 'Иконки и внизу текст'),
        ('icons_plus_cat_full', 'Иконки+Категории(полная вер.)'),
        ('icons', 'Только иконки'),
    ]

    MOBILE_GRID_CHOICES = [(0, 'Как на десктопе (адаптивный от разрешения экрана)'), (1, 'Одна колонка'),
                           (2, 'Две колонки'), (3, 'Три колонки'),
                           (4, 'Четыре колонки'), ]

    SLIDER_EFFECT_CHOICES = [('slide', 'Пролистывание'), ('fade', 'Наплыв'), ('cube', '3D Куб'),
                             ('flip', '3D Переворот')]

    # --- Основные настройки ---
    shop_name = models.CharField("Название магазина", max_length=100, default="MegaCvet")
    contact_phone = models.CharField("Контактный телефон", max_length=50, blank=True)
    admin_notification_emails = models.TextField("Email для уведомлений", blank=True,
                                                 help_text="Можно указать несколько адресов через запятую.")
    background_image = models.ImageField("Фоновое изображение", upload_to='backgrounds/', blank=True, null=True)
    delivery_cost = models.DecimalField("Стоимость доставки", max_digits=10, decimal_places=2, default=300.00,
                                        help_text="Стоимость доставки будет добавлена к общей сумме заказа.")

    # --- Настройки каталога и товара ---
    all_products_text = models.CharField("Текст ссылки 'Все товары'", max_length=50, default="Все товары")

    # Каталог
    catalog_title = models.CharField("Заголовок страницы каталога", max_length=200, default='Наш каталог цветов',
                                     help_text="Отображается на странице 'Все товары'")
    catalog_title_color = models.CharField("Цвет заголовка каталога", max_length=7, blank=True, default='')
    catalog_title_font_family = models.CharField("Шрифт заголовка каталога", max_length=50,
                                                 choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True, default='')
    catalog_title_font_style = models.CharField("Начертание заголовка каталога", max_length=20,
                                                choices=FONT_STYLE_CHOICES, default='bold')

    # Популярные
    popular_title = models.CharField("Заголовок (Популярные)", max_length=200, default='Популярные букеты',
                                     help_text="Заголовок блока на главной странице")
    popular_title_color = models.CharField("Цвет заголовка (Популярные)", max_length=7, blank=True, default='')
    popular_title_font_family = models.CharField("Шрифт (Популярные)", max_length=50,
                                                 choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True, default='')
    popular_title_font_style = models.CharField("Начертание (Популярные)", max_length=20, choices=FONT_STYLE_CHOICES,
                                                default='bold')

    default_composition_title = models.CharField("Заголовок 'Состава' (по умолч.)", max_length=100, default="Состав")
    default_description_title = models.CharField("Заголовок 'Описания' (по умолч.)", max_length=100, default="Описание")

    # --- Настройки слайдера ---
    slider_duration = models.PositiveIntegerField("Пауза (сек)", default=5)
    slider_effect = models.CharField("Эффект", max_length=10, choices=SLIDER_EFFECT_CHOICES, default='slide')

    # --- Глобальное оформление ---
    navigation_style = models.CharField("Стиль анимации навигации", max_length=10, choices=NAV_STYLE_CHOICES,
                                        default='underline', help_text="Эффект при наведении на ссылки в меню.")
    icon_animation_style = models.CharField("Стиль анимации иконок", max_length=10, choices=ICON_ANIMATION_CHOICES,
                                            default='scale', help_text="Эффект при наведении на иконки в шапке.")

    # Шрифты и цвета
    default_font_family = models.CharField("Шрифт", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, default='roboto')
    default_font_size = models.PositiveIntegerField("Размер (px)", default=16)
    default_text_color = models.CharField("Цвет шрифта", max_length=7, default='#333333', blank=True,
                                          help_text="Сброс к значению по умолчанию: очистите поле (нажмите ×)")

    logo_font_family = models.CharField("Шрифт", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True,
                                        default='')
    logo_font_size = models.PositiveIntegerField("Размер (px)", blank=True, null=True)
    logo_font_style = models.CharField("Начертание", max_length=20, choices=FONT_STYLE_CHOICES, default='bold')
    logo_color = models.CharField("Цвет", max_length=7, blank=True, default='')

    icon_size = models.PositiveIntegerField("Размер (px)", blank=True, null=True)
    icon_color = models.CharField("Цвет", max_length=7, blank=True, default='')

    category_font_family = models.CharField("Шрифт", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True,
                                            default='')
    category_font_size = models.PositiveIntegerField("Размер (px)", blank=True, null=True)
    category_font_style = models.CharField("Начертание", max_length=20, choices=FONT_STYLE_CHOICES, default='normal')
    category_text_color = models.CharField("Цвет шрифта", max_length=7, blank=True, default='')

    footer_font_family = models.CharField("Шрифт", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True,
                                          default='')
    footer_font_size = models.PositiveIntegerField("Размер (px)", blank=True, null=True)
    footer_font_style = models.CharField("Начертание", max_length=20, choices=FONT_STYLE_CHOICES, default='normal')
    footer_text_color = models.CharField("Цвет шрифта", max_length=7, blank=True, default='')

    product_title_font_family = models.CharField("Шрифт", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True,
                                                 default='')
    product_title_font_size = models.PositiveIntegerField("Размер (px)", blank=True, null=True)
    product_title_font_style = models.CharField("Начертание", max_length=20, choices=FONT_STYLE_CHOICES,
                                                default='normal')
    product_title_text_color = models.CharField("Цвет шрифта", max_length=7, blank=True, default='')

    product_header_font_family = models.CharField("Шрифт", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES,
                                                  blank=True, default='')
    product_header_font_size = models.PositiveIntegerField("Размер (px)", blank=True, null=True)
    product_header_font_style = models.CharField("Начертание", max_length=20, choices=FONT_STYLE_CHOICES,
                                                 default='bold')
    product_header_text_color = models.CharField("Цвет шрифта", max_length=7, blank=True, default='')

    accent_color = models.CharField("Акцентный цвет (кнопки)", max_length=7, default='#e53935', blank=True)
    heading_font_family = models.CharField("Шрифт для заголовков", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES,
                                           default='montserrat')
    heading_font_style = models.CharField("Начертание заголовков", max_length=20, choices=FONT_STYLE_CHOICES,
                                          default='bold')

    # Старые
    main_text_color = models.CharField("Основной цвет текста (устарело)", max_length=7, default='#333333',
                                       editable=False)
    body_font_family = models.CharField("Шрифт для основного текста (устарело)", max_length=50,
                                        choices=GLOBAL_FONT_FAMILY_CHOICES, default='roboto', editable=False)
    base_font_size = models.PositiveIntegerField("Базовый размер шрифта (устарело, px)", default=16, editable=False)

    # --- Кнопки ---
    button_bg_color = models.CharField("Цвет фона", max_length=7, blank=True, default='')
    button_text_color = models.CharField("Цвет текста", max_length=7, blank=True, default='')
    button_hover_bg_color = models.CharField("Цвет фона при наведении", max_length=7, blank=True, default='')
    button_border_radius = models.PositiveIntegerField("Скругление углов (px)", blank=True, null=True)
    button_font_family = models.CharField("Стиль шрифта", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True,
                                          default='')
    button_font_style = models.CharField("Начертание", max_length=20, choices=FONT_STYLE_CHOICES, default='bold')
    add_to_cart_bg_color = models.CharField("Цвет фона кнопки 'В корзину'", max_length=7, blank=True, default='')
    add_to_cart_text_color = models.CharField("Цвет текста кнопки 'В корзину'", max_length=7, blank=True, default='')
    add_to_cart_hover_bg_color = models.CharField("Цвет фона 'В корзину' при наведении", max_length=7, blank=True,
                                                  default='')

    # --- Мобильная версия ---

    mobile_header_style = models.CharField("Отображение ссылок в шапке", max_length=25, choices=MOBILE_HEADER_CHOICES,
                                           default='partial')
    mobile_product_grid = models.PositiveSmallIntegerField("Кол-во товаров в ряду", choices=MOBILE_GRID_CHOICES,
                                                           default=2)

    # === ИЗМЕНЕНО: ВАЛИДАТОРЫ [-50, 50] ===
    mobile_font_scale = models.IntegerField(
        "Корректировка размера заголовков", default=0, blank=True,
        validators=[MinValueValidator(-50), MaxValueValidator(50)],
        help_text="0% - стандарт (по центру). Влево до -50%, вправо до +50%."
    )

    collapse_categories_threshold = models.PositiveSmallIntegerField("Схлопывать категории в иконку", default=4)
    collapse_footer_threshold = models.PositiveSmallIntegerField("Схлопывать ссылки в подвале", default=4)

    mobile_dropdown_bg_color = models.CharField("Фон", max_length=7, blank=True, default='')
    mobile_dropdown_opacity = models.FloatField("Прозрачность фона", default=95, blank=True, null=True,
                                                validators=[MinValueValidator(0), MaxValueValidator(100)])
    mobile_dropdown_font_family = models.CharField("Стиль шрифта", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES,
                                                   blank=True, default='')
    mobile_dropdown_font_size = models.PositiveSmallIntegerField("Размер шрифта (px)", blank=True, null=True)
    mobile_dropdown_font_style = models.CharField("Начертание", max_length=20, choices=FONT_STYLE_CHOICES,
                                                  default='normal')
    mobile_dropdown_view_mode = models.CharField("Вид информации", max_length=20, choices=MENU_VIEW_MODE_CHOICES,
                                                 default='text')
    mobile_dropdown_font_color = models.CharField("Цвет текста", max_length=7, blank=True, default='')
    mobile_dropdown_button_bg_color = models.CharField("Цвет фона кнопок", max_length=7, blank=True, default='')
    mobile_dropdown_button_text_color = models.CharField("Цвет текста кнопок", max_length=7, blank=True, default='')
    mobile_dropdown_button_border_radius = models.PositiveSmallIntegerField("Скругление кнопок (px)", blank=True,
                                                                            null=True)
    mobile_dropdown_button_opacity = models.FloatField("Прозрачность кнопок", default=100, blank=True, null=True,
                                                       validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        verbose_name = "Настройки сайта"

    def __str__(self):
        return "Настройки сайта"

    @property
    def mobile_dropdown_opacity_css(self):
        val = self.mobile_dropdown_opacity if self.mobile_dropdown_opacity is not None else 95
        return str(val / 100).replace(',', '.')

    @property
    def mobile_font_scale_css(self):
        val = self.mobile_font_scale if self.mobile_font_scale is not None else 0
        factor = 1 + (val / 100)
        return str(factor).replace(',', '.')

    @property
    def mobile_dropdown_bg_rgb(self):
        hex_color = (self.mobile_dropdown_bg_color or '#FFFFFF').lstrip('#')
        try:
            return ", ".join(str(int(hex_color[i:i + 2], 16)) for i in (0, 2, 4))
        except (ValueError, IndexError):
            return "255, 255, 255"

    @property
    def mobile_dropdown_button_opacity_css(self):
        val = self.mobile_dropdown_button_opacity if self.mobile_dropdown_button_opacity is not None else 100
        return str(val / 100).replace(',', '.')

    @property
    def mobile_dropdown_button_bg_rgb(self):
        hex_color = (self.mobile_dropdown_button_bg_color or self.button_bg_color or self.accent_color).lstrip('#')
        try:
            return ", ".join(str(int(hex_color[i:i + 2], 16)) for i in (0, 2, 4))
        except (ValueError, IndexError):
            return "229, 57, 53"


class FooterPage(models.Model):
    title = models.CharField("Название ссылки", max_length=50)
    page_title = models.CharField("Заголовок на странице", max_length=200, blank=True)
    slug = models.SlugField("URL-адрес", unique=True)
    content = models.TextField("Содержимое страницы", blank=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Страница в футере"
        verbose_name_plural = "Страницы в футере"

    def __str__(self): return self.title

    def get_absolute_url(self): return reverse('shop:footer_page_detail', args=[self.slug])

    def get_page_title(self): return self.page_title or self.title


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created: Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'): instance.profile.save()