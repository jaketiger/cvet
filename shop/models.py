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
from django.utils.html import format_html # Добавил для админки, если пригодится

# --- КОНСТАНТЫ ВЫБОРА ---

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

DESKTOP_HEADER_BEHAVIOR = [
    ('normal', 'Обычная (скрывается при прокрутке)'),
    ('sticky_all', 'Фиксировать Шапку + Категории'),
    ('sticky_header', 'Фиксировать только Шапку'),
    ('sticky_nav', 'Фиксировать только Категории'),
]

MOBILE_HEADER_BEHAVIOR = [
    ('normal', 'Обычная (скрывается при прокрутке)'),
    ('sticky', 'Фиксированная (всегда сверху)'),
]

DESKTOP_CAT_BG_MODE = [
    ('custom', 'Свой цвет (выбрать палитрой)'),
    ('sheet', 'Фон листа сайта'),
    ('header', 'Как в шапке'),
]

MOBILE_HEADER_BG_MODE = [
    ('custom', 'Свой цвет (выбрать палитрой)'),
    ('sheet', 'Фон листа сайта'),
]

BUTTON_PRESET_CHOICES = [
    ('standard', 'Стандарт (Плоские, слегка скругленные)'),
    ('pill', 'Таблетка (Круглые края)'),
    ('soft', 'Soft UI (Неоморфизм, мягкие тени)'),
    ('gradient', 'Градиент (Яркий перелив + Анимация)'),
    ('glass_frosted', 'Матовое стекло (Frosted Glass)'),
    ('neon_pulse', 'Неон Пульс (Свечение + Анимация)'),
    ('brutal', 'Брутализм (Жесткие черные тени)'),
    ('pushable_3d', '3D Нажатие (Эффект нажатия)'),
    ('shine_hover', 'Блеск (Перелив при наведении)'),
    ('outline_fill', 'Контур (Заливка при наведении)'),
]

SLIDER_EFFECT_CHOICES = [
    ('slide', 'Пролистывание (Slide)'),
    ('fade', 'Наплыв (Fade)'),
    ('cube', '3D Куб (Cube)'),
    ('flip', '3D Переворот (Flip)'),
    ('coverflow', '3D Карусель (Coverflow)'),
    ('cards', 'Карточки (Стопкой)'),
    ('creative_one', 'Креативный (Перспектива)'),
    ('creative_two', 'Креативный (Сдвиг справа)'),
    ('creative_three', 'Креативный (Вращение)'),
]

HELP_COLOR_RESET = "Сброс к значению по умолчанию: очистите поле (нажмите × в палитре)."
HELP_OPACITY = "0% - полностью прозрачный, 100% - полностью непрозрачный."
HELP_BLUR = "0px - нет размытия. Увеличивайте для эффекта матового стекла."


class Category(models.Model):
    name = models.CharField("Название категории", max_length=200)
    slug = models.SlugField("URL", max_length=200, unique=True)
    order = models.PositiveIntegerField("Порядок", default=0, help_text="Чем меньше число, тем левее категория в меню")

    class Meta:
        ordering = ['order']
        indexes = [models.Index(fields=['name']), ]
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])


class Product(models.Model):
    category = models.ManyToManyField(Category, related_name='products', blank=True, verbose_name="Категории")
    name = models.CharField("Название товара", max_length=200)
    slug = models.SlugField("URL", max_length=200)
    image = models.ImageField(upload_to='products/%Y/%m/%d', blank=True, verbose_name="Основное изображение")
    image_thumbnail = ImageSpecField(source='image', processors=[ResizeToFill(300, 250)], format='JPEG', options={'quality': 80})
    composition_title = models.CharField("Заголовок для 'Состава'", max_length=100, blank=True, help_text="Если пусто, будет использован заголовок из Настроек сайта.")
    composition = models.TextField("Состав (блок под фото)", blank=True)
    description_title = models.CharField("Заголовок для 'Описания'", max_length=100, blank=True, help_text="Если пусто, будет использован заголовок из Настроек сайта.")
    description = models.TextField("Описание (блок справа от фото)", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    stock = models.PositiveIntegerField(verbose_name="Остаток на складе")
    available = models.BooleanField(default=True, verbose_name="Доступен для заказа")
    is_featured = models.BooleanField(default=False, verbose_name="Показывать на главной")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        ordering = ['name']
        indexes = [models.Index(fields=['id', 'slug']), models.Index(fields=['name']), models.Index(fields=['-created'])]
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name='Товар')
    image = models.ImageField(upload_to='products/gallery/%Y/%m/%d', verbose_name='Изображение')
    image_thumbnail = ImageSpecField(source='image', processors=[ResizeToFill(100, 100)], format='JPEG', options={'quality': 70})
    alt_text = models.CharField(max_length=255, blank=True, verbose_name='Альтернативный текст (для SEO)')

    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
        ordering = ['id']

    def __str__(self):
        return f"Изображение для {self.product.name}"


class Banner(models.Model):
    CONTENT_POSITION_CHOICES = [
        ('center-center', 'По центру'),
        ('bottom-left', 'Внизу слева'),
        ('bottom-right', 'Внизу справа'),
        ('top-left', 'Вверху слева'),
        ('top-right', 'Вверху справа')
    ]
    image = models.ImageField("Изображение (1600x600)", upload_to='banners/')
    title = models.CharField("Заголовок (необязательно)", max_length=200, blank=True)
    subtitle = models.CharField("Подзаголовок (необязательно)", max_length=300, blank=True)
    link = models.URLField("Ссылка (URL, необязательно)", blank=True)
    button_text = models.CharField("Текст на кнопке (необязательно)", max_length=50, blank=True, help_text="Если пусто, весь баннер будет ссылкой.")
    content_position = models.CharField("Расположение текста", max_length=20, choices=CONTENT_POSITION_CHOICES, default='center-center')
    background_opacity = models.FloatField("Прозрачность фона текста", default=45, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text="0% - прозрачный, 100% - черный фон.")
    font_color = models.CharField("Цвет шрифта", max_length=7, blank=True, help_text=HELP_COLOR_RESET)
    font_family = models.CharField("Стиль шрифта", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, default='roboto')
    is_active = models.BooleanField("Активен", default=True, help_text="Только активные баннеры будут показаны.")
    order = models.PositiveIntegerField("Порядок", default=0, help_text="Чем меньше число, тем раньше.")

    @property
    def background_opacity_css(self):
        return self.background_opacity / 100

    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"
        ordering = ['order']

    def __str__(self):
        return self.title or f"Баннер #{self.id}"


class Benefit(models.Model):
    title = models.CharField("Заголовок", max_length=100, help_text="Например: Свежие цветы, Быстрая доставка")
    description = models.TextField("Описание (всплывашка)", blank=True, help_text="Текст, который появится при наведении (необязательно)")
    icon_svg = models.TextField("SVG иконка", help_text="Вставьте сюда полный код <svg>...</svg> для иконки.")
    is_active = models.BooleanField("Активно", default=True)
    order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        ordering = ['order']
        verbose_name = "Преимущество (в карточке)"
        verbose_name_plural = "Преимущества (иконка в карточке Товара)"

    def __str__(self):
        return self.title


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField("Телефон", max_length=20, blank=True)
    address = models.CharField("Адрес", max_length=250, blank=True)
    postal_code = models.CharField("Индекс", max_length=20, blank=True)
    city = models.CharField("Город", max_length=100, blank=True)

    def __str__(self):
        return f'Профиль пользователя {self.user.username}'


class SiteSettings(SingletonModel):
    # Выборы
    NAV_STYLE_CHOICES = [('underline', 'Анимация подчеркивания'), ('highlight', 'Фоновая подсветка'),
                         ('lift', 'Эффект приподнимания'), ('shadow', 'Сдвиг с тенью (3D)'), ('wave', '"Жидкая" волна')]

    # --- ОБНОВЛЕННЫЙ СПИСОК АНИМАЦИЙ ---
    ICON_ANIMATION_CHOICES = [
        ('scale', 'Увеличение (стандарт)'),
        ('rotate', 'Вращение'),
        ('bounce', 'Подпрыгивание'),
        ('shake', 'Тряска (Shake)'),  # Новое
        ('pulse', 'Пульсация (Pulse)'),  # Новое
        ('swing', 'Качание (Swing)'),  # Новое
    ]
    MOBILE_HEADER_CHOICES = [('partial', 'Иконки и внизу текст'), ('icons_plus_cat_full', 'Иконки+Категории(полная вер.)'), ('icons', 'Только иконки')]
    MOBILE_GRID_CHOICES = [(0, 'Как на десктопе (адаптивный от разрешения экрана)'), (1, 'Одна колонка'), (2, 'Две колонки'), (3, 'Три колонки'), (4, 'Четыре колонки')]

    # Основные настройки
    shop_name = models.CharField("Название магазина", max_length=100, default="MegaCvet")
    contact_phone = models.CharField("Контактный телефон", max_length=50, blank=True)
    contact_phone_secondary = models.CharField("Телефон (Дополнительный)", max_length=50, blank=True)
    pickup_address = models.TextField("Адрес самовывоза", blank=True, help_text="Отображается на странице Контакты")
    working_hours = models.TextField("Режим работы", blank=True, help_text="Каждый день с новой строки")
    map_embed_code = models.TextField("HTML-код карты для страницы 'Контакты'", blank=True, help_text="Вставьте сюда код виджета с Яндекс.Карт или Google Maps.")
    contacts_page_title = models.CharField("Заголовок страницы контактов", max_length=100, default="Контактная информация")
    contacts_address_title = models.CharField("Заголовок 'Адрес'", max_length=100, default="Адрес для самовывоза:")
    contacts_hours_title = models.CharField("Заголовок 'График'", max_length=100, default="График работы:")
    contacts_phone_title = models.CharField("Заголовок 'Телефон'", max_length=100, default="Телефон для связи:")
    admin_notification_emails = models.TextField("Email для уведомлений", blank=True, help_text="Можно указать несколько адресов через запятую.")
    background_image = models.ImageField("Фоновое изображение", upload_to='backgrounds/', blank=True, null=True)
    delivery_cost = models.DecimalField("Стоимость доставки", max_digits=10, decimal_places=2, default=300.00, help_text="Стоимость доставки будет добавлена к общей сумме заказа.")

    # Фон листа
    site_sheet_bg_color = models.CharField("Фон листа сайта", max_length=7, blank=True, default='#ffffff', help_text=HELP_COLOR_RESET + " Если очистить, фон будет прозрачным.")
    site_sheet_opacity = models.FloatField("Прозрачность листа", default=95, blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text=HELP_OPACITY)
    site_sheet_blur = models.PositiveIntegerField("Размытие фона листа (px)", default=0, blank=True, null=True, validators=[MaxValueValidator(20)], help_text=HELP_BLUR)

    # Шапка
    desktop_header_behavior = models.CharField("Поведение (Десктоп)", max_length=20, choices=DESKTOP_HEADER_BEHAVIOR, default='normal')
    desktop_header_scroll_enabled = models.BooleanField("Прозрачность Шапки при скролле", default=False)
    desktop_header_scroll_opacity = models.FloatField("Прозрачность Шапки", default=90, blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text=HELP_OPACITY)
    desktop_header_blur = models.PositiveIntegerField("Размытие Шапки (px)", default=0, blank=True, null=True, validators=[MaxValueValidator(20)], help_text=HELP_BLUR)
    desktop_category_scroll_enabled = models.BooleanField("Прозрачность Категорий при скролле", default=False)
    desktop_categories_bg_mode = models.CharField("Режим фона Категорий", max_length=20, choices=DESKTOP_CAT_BG_MODE, default='sheet')
    desktop_categories_bg_color = models.CharField("Свой цвет Категорий", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    desktop_categories_opacity = models.FloatField("Прозрачность Категорий", default=100, blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text=HELP_OPACITY)
    desktop_category_blur = models.PositiveIntegerField("Размытие Категорий (px)", default=0, blank=True, null=True, validators=[MaxValueValidator(20)], help_text=HELP_BLUR)
    mobile_header_behavior = models.CharField("Поведение (Мобильный)", max_length=20, choices=MOBILE_HEADER_BEHAVIOR, default='normal')
    mobile_header_transparent_scroll = models.BooleanField("Прозрачность при скролле", default=False)
    mobile_header_scroll_opacity = models.FloatField("Прозрачность", default=90, blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text=HELP_OPACITY)
    mobile_header_blur = models.PositiveIntegerField("Размытие (px)", default=0, blank=True, null=True, validators=[MaxValueValidator(20)], help_text=HELP_BLUR)
    mobile_header_bg_mode = models.CharField("Режим фона", max_length=20, choices=MOBILE_HEADER_BG_MODE, default='sheet')
    mobile_header_bg_color_custom = models.CharField("Свой цвет", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)

    # Каталог и товары
    all_products_text = models.CharField("Текст ссылки 'Все товары'", max_length=50, default="Все товары")
    catalog_title = models.CharField("Заголовок страницы каталога", max_length=200, default='Наш каталог цветов')
    catalog_title_color = models.CharField("Цвет заголовка каталога", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    catalog_title_font_family = models.CharField("Шрифт заголовка каталога", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True, default='')
    catalog_title_font_style = models.CharField("Начертание заголовка каталога", max_length=20, choices=FONT_STYLE_CHOICES, default='bold')
    popular_title = models.CharField("Заголовок (Популярные)", max_length=200, default='Популярные букеты')
    popular_title_color = models.CharField("Цвет заголовка (Популярные)", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    popular_title_font_family = models.CharField("Шрифт (Популярные)", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True, default='')
    popular_title_font_style = models.CharField("Начертание (Популярные)", max_length=20, choices=FONT_STYLE_CHOICES, default='bold')
    default_composition_title = models.CharField("Заголовок 'Состава' (по умолч.)", max_length=100, default="Состав")
    default_description_title = models.CharField("Заголовок 'Описания' (по умолч.)", max_length=100, default="Описание")

    # Слайдер
    slider_duration = models.PositiveIntegerField("Пауза (сек)", default=5)
    slider_effect = models.CharField("Эффект", max_length=20, choices=SLIDER_EFFECT_CHOICES, default='slide')

    # Глобальное оформление
    navigation_style = models.CharField("Стиль анимации навигации", max_length=10, choices=NAV_STYLE_CHOICES, default='underline', help_text="Эффект при наведении на ссылки в меню.")
    icon_animation_style = models.CharField("СТИЛЬ АНИМАЦИИ ИКОНОК", max_length=10, choices=ICON_ANIMATION_CHOICES, default='scale', help_text="Эффект при наведении на иконки в шапке.")
    default_font_family = models.CharField("Шрифт (Основной текст)", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, default='roboto')
    default_font_size = models.PositiveIntegerField("Размер (Основной текст, px)", default=16)
    default_text_color = models.CharField("Цвет шрифта (Основной)", max_length=7, default='#333333', blank=True, help_text=HELP_COLOR_RESET)
    logo_font_family = models.CharField("Шрифт (Логотип)", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True, default='')
    logo_font_size = models.PositiveIntegerField("Размер (Логотип, px)", blank=True, null=True)
    logo_font_style = models.CharField("Начертание (Логотип)", max_length=20, choices=FONT_STYLE_CHOICES, default='bold')
    logo_color = models.CharField("Цвет (Логотип)", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    icon_size = models.PositiveIntegerField("Размер иконок (Шапка, px)", blank=True, null=True)
    icon_color = models.CharField("Цвет иконок (Шапка)", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    category_font_family = models.CharField("Шрифт (Меню категорий)", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True, default='')
    category_font_size = models.PositiveIntegerField("Размер (Меню категорий, px)", blank=True, null=True)
    category_font_style = models.CharField("Начертание (Меню категорий)", max_length=20, choices=FONT_STYLE_CHOICES, default='normal')
    category_text_color = models.CharField("Цвет текста (Меню категорий)", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    footer_font_family = models.CharField("Шрифт (Подвал/Footer)", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True, default='')
    footer_font_size = models.PositiveIntegerField("Размер (Подвал, px)", blank=True, null=True)
    footer_font_style = models.CharField("Начертание (Подвал)", max_length=20, choices=FONT_STYLE_CHOICES, default='normal')
    footer_text_color = models.CharField("Цвет текста (Подвал)", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    product_title_font_family = models.CharField("Шрифт (Название товара)", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True, default='')
    product_title_font_size = models.PositiveIntegerField("Размер (Название товара, px)", blank=True, null=True)
    product_title_font_style = models.CharField("Начертание (Название товара)", max_length=20, choices=FONT_STYLE_CHOICES, default='normal')
    product_title_text_color = models.CharField("Цвет текста (Название товара)", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    product_header_font_family = models.CharField("Шрифт (Заголовки описания)", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True, default='')
    product_header_font_size = models.PositiveIntegerField("Размер (Заголовки описания, px)", blank=True, null=True)
    product_header_font_style = models.CharField("Начертание (Заголовки описания)", max_length=20, choices=FONT_STYLE_CHOICES, default='bold')
    product_header_text_color = models.CharField("Цвет текста (Заголовки описания)", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    heading_font_family = models.CharField("Шрифт для заголовков (H1, H2...)", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, default='montserrat')
    heading_font_size = models.PositiveIntegerField("Размер заголовков (H1, px)", default=24, blank=True, null=True)
    heading_font_style = models.CharField("Начертание заголовков", max_length=20, choices=FONT_STYLE_CHOICES, default='bold')
    accent_color = models.CharField("Акцентный цвет (Глобальный)", max_length=7, default='#e53935', blank=True)

    main_text_color = models.CharField("Основной цвет текста (устарело)", max_length=7, default='#333333', editable=False)
    body_font_family = models.CharField("Шрифт для основного текста (устарело)", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, default='roboto', editable=False)
    base_font_size = models.PositiveIntegerField("Базовый размер шрифта (устарело, px)", default=16, editable=False)

    # Кнопки
    button_style_preset = models.CharField("Стиль кнопок (Пресет)", max_length=20, choices=BUTTON_PRESET_CHOICES, default='standard')
    button_bg_color = models.CharField("Цвет фона", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    button_accent_color = models.CharField("Акцентный цвет КНОПОК", max_length=7, blank=True, default='')
    button_text_color = models.CharField("Цвет текста", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    button_hover_bg_color = models.CharField("Цвет фона при наведении", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    button_border_radius = models.PositiveIntegerField("Скругление углов (px)", blank=True, null=True)
    button_font_family = models.CharField("Стиль шрифта", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True, default='')
    button_font_style = models.CharField("Начертание", max_length=20, choices=FONT_STYLE_CHOICES, default='bold')
    add_to_cart_bg_color = models.CharField("Цвет фона кнопки 'В корзину'", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    add_to_cart_text_color = models.CharField("Цвет текста кнопки 'В корзину'", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    add_to_cart_hover_bg_color = models.CharField("Цвет фона 'В корзину' при наведении", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)

    # Мобильная версия
    mobile_header_style = models.CharField("Отображение ссылок в шапке", max_length=25, choices=MOBILE_HEADER_CHOICES, default='partial')
    mobile_product_grid = models.PositiveSmallIntegerField("Кол-во товаров в ряду", choices=MOBILE_GRID_CHOICES, default=2)
    mobile_font_scale = models.IntegerField("Корректировка размера заголовков", default=0, blank=True, validators=[MinValueValidator(-1000), MaxValueValidator(1000)])
    collapse_categories_threshold = models.PositiveSmallIntegerField("Схлопывать категории в иконку", default=4)
    collapse_footer_threshold = models.PositiveSmallIntegerField("Схлопывать ссылки в подвале", default=4)

    # Мобильное меню
    mobile_button_override_global = models.BooleanField("Применить мобильные цвета ко ВСЕМ кнопкам", default=False)
    mobile_dropdown_bg_color = models.CharField("Фон", max_length=7, blank=True, default='', help_text=HELP_COLOR_RESET)
    mobile_dropdown_opacity = models.FloatField("Прозрачность фона", default=95, blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text=HELP_OPACITY)
    mobile_dropdown_font_family = models.CharField("Стиль шрифта", max_length=50, choices=GLOBAL_FONT_FAMILY_CHOICES, blank=True, default='')
    mobile_dropdown_font_size = models.PositiveSmallIntegerField("Размер шрифта (px)", blank=True, null=True)
    mobile_dropdown_font_style = models.CharField("Начертание", max_length=20, choices=FONT_STYLE_CHOICES, default='normal')
    mobile_dropdown_view_mode = models.CharField("Вид информации", max_length=20, choices=MENU_VIEW_MODE_CHOICES, default='text')
    mobile_dropdown_font_color = models.CharField("Цвет текста (ВСЕ)", max_length=7, blank=True, default='')
    mobile_dropdown_button_bg_color = models.CharField("Цвет фона кнопок (ВСЕ)", max_length=7, blank=True, default='')
    mobile_dropdown_button_text_color = models.CharField("Цвет текста кнопок (ВСЕ)", max_length=7, blank=True, default='')

#    mobile_dropdown_button_border_radius = models.PositiveSmallIntegerField("Скругление кнопок (px)", blank=True, null=True)
#    mobile_dropdown_button_opacity = models.FloatField("Прозрачность кнопок", default=100, blank=True, null=True, validators=[MinValueValidator(0), MaxValueValidator(100)], help_text=HELP_OPACITY)
    mobile_dropdown_inherit_radius = models.BooleanField("Использовать глобальное скругление?", default=True,
                                                         help_text="Если галочка стоит, скругление будет таким же, как у всех кнопок на сайте. Если снята — используется значение из поля ниже.")
    mobile_dropdown_button_border_radius = models.PositiveSmallIntegerField("Скругление кнопок (px)", blank=True,
                                                                            null=True,
                                                                            help_text="Сработает, только если галочка слева снята.")
    mobile_dropdown_button_opacity = models.FloatField("Прозрачность кнопок", default=100, blank=True, null=True,
                                                       validators=[MinValueValidator(0), MaxValueValidator(100)],
                                                       help_text="100% - непрозрачные, 0% - полностью прозрачные.")

    # Статические страницы
    static_page_title_color = models.CharField(
        "Цвет заголовков H1",
        max_length=7,
        blank=True,
        help_text="Меняет цвет заголовков на страницах 'Контакты', 'О нас' и текстовых страницах."
    )
    static_page_subtitle_color = models.CharField(
        "Цвет подзаголовков H3",
        max_length=7,
        blank=True,
        help_text="Цвет заголовков блоков (например, 'Адрес', 'Телефон', 'Режим работы')."
    )
    static_page_icon_color = models.CharField(
        "Цвет иконок",
        max_length=7,
        blank=True,
        help_text="Цвет SVG иконок (телефон, маркер карты, часы) на странице контактов."
    )
    static_page_link_color = models.CharField(
        "Цвет ссылок",
        max_length=7,
        blank=True,
        help_text="Цвет кликабельных элементов (номера телефонов, email)."
    )
    static_page_link_hover_color = models.CharField(
        "Цвет ссылок при наведении",
        max_length=7,
        blank=True,
        help_text="В какой цвет окрашивается ссылка, когда на неё наводят мышку."
    )

    class Meta:
        verbose_name = "Настройки сайта"

    def __str__(self):
        return "Настройки сайта"

    def _get_rgb(self, hex_color):
        if not hex_color: return '255, 255, 255'
        h = hex_color.lstrip('#')
        try:
            return ", ".join(str(int(h[i:i+2], 16)) for i in (0, 2, 4))
        except:
            return '255, 255, 255'

    @property
    def sheet_bg_rgb(self): return self._get_rgb(self.site_sheet_bg_color)
    @property
    def sheet_opacity_css(self): return str((self.site_sheet_opacity if self.site_sheet_opacity is not None else 95)/100).replace(',', '.')
    @property
    def desktop_header_opacity_css(self): return str((self.desktop_header_scroll_opacity if self.desktop_header_scroll_opacity is not None else 90)/100).replace(',', '.')
    @property
    def mobile_header_opacity_css(self): return str((self.mobile_header_scroll_opacity if self.mobile_header_scroll_opacity is not None else 90)/100).replace(',', '.')
    @property
    def desktop_cat_opacity_css(self): return str((self.desktop_categories_opacity if self.desktop_categories_opacity is not None else 100)/100).replace(',', '.')
    @property
    def mobile_dropdown_opacity_css(self): return str((self.mobile_dropdown_opacity if self.mobile_dropdown_opacity is not None else 95)/100).replace(',', '.')
    @property
    def mobile_font_scale_css(self): return str(1 + ((self.mobile_font_scale if self.mobile_font_scale is not None else 0)/100)).replace(',', '.')
    @property
    def mobile_dropdown_bg_rgb(self): return self._get_rgb(self.mobile_dropdown_bg_color or '#FFFFFF')
    @property
    def mobile_dropdown_button_opacity_css(self): return str((self.mobile_dropdown_button_opacity if self.mobile_dropdown_button_opacity is not None else 100)/100).replace(',', '.')
    @property
    def mobile_dropdown_button_bg_rgb(self): return self._get_rgb(self.mobile_dropdown_button_bg_color or self.button_bg_color or self.accent_color)
    @property
    def mobile_dropdown_button_text_color_css(self): return self.mobile_dropdown_button_text_color or self.button_text_color or '#FFFFFF'
    @property
    def desktop_cat_bg_rgb(self): return self._get_rgb(self.desktop_categories_bg_color) if self.desktop_categories_bg_mode=='custom' else self._get_rgb(self.site_sheet_bg_color) if self.desktop_categories_bg_mode=='sheet' else '255, 255, 255'
    @property
    def mobile_header_bg_rgb(self): return self._get_rgb(self.mobile_header_bg_color_custom) if self.mobile_header_bg_mode=='custom' else self._get_rgb(self.site_sheet_bg_color) if self.mobile_header_bg_mode=='sheet' else '255, 255, 255'


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


class Postcard(models.Model):
    # НОВАЯ МОДЕЛЬ ОТКРЫТКИ
    title = models.CharField("Название", max_length=100)
    image = models.ImageField("Изображение открытки", upload_to='postcards/')
    price = models.DecimalField("Цена (0 = бесплатно)", max_digits=10, decimal_places=2, default=0.00)
    order = models.PositiveIntegerField("Порядок сортировки", default=0)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = 'Открытка'
        verbose_name_plural = 'Открытки (для заказа)'
        ordering = ['order', 'price'] # Сначала по порядку, потом по цене

    def __str__(self):
        type_str = "Платная" if self.price > 0 else "Бесплатная"
        return f"{self.title} ({type_str})"