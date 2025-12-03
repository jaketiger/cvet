# shop/admin.py

from django import forms
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import path
from django.shortcuts import redirect
from django.conf import settings
from django.http import FileResponse
from django.core.management import call_command
from django.contrib import messages
import os
import subprocess
import zipfile
import io
from io import StringIO
from .forms import PostcardSettingsForm

from solo.admin import SingletonModelAdmin
from adminsortable2.admin import SortableAdminMixin

from .models import (Category, Product, SiteSettings, FooterPage, ProductImage, Banner, Benefit, Postcard)
from .forms import SiteSettingsForm, BannerAdminForm, ProductAdminForm, SliderSettingsForm


# === 1. МИКСИН СТИЛЕЙ ===
class ShopAdminStyleMixin:
    """
    Добавляет кнопки сверху и подключает CSS.
    """
    save_on_top = True
    change_list_template = "admin/change_list_save_top.html"

    # Используем class Media для безопасного объединения
    class Media:
        css = {'all': ('shop/css/admin_custom_buttons.css',)}


# === 2. МОДЕЛИ ===

@admin.register(Postcard)
class PostcardAdmin(SortableAdminMixin, ShopAdminStyleMixin, admin.ModelAdmin):

    # Подключаем наш шаблон
    change_list_template = "admin/shop/postcard/change_list_custom.html"

    list_display = ('title', 'preview', 'price', 'is_active', 'order')
    list_editable = ('price', 'is_active')

    # Сортировка
    default_order_field = 'order'

    list_filter = ('is_active',)
    list_display_links = ('title', 'preview')

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 50px; border-radius: 4px;" />', obj.image.url)
        return "-"

    preview.short_description = "Фото"


# === ЛОГИКА ДЛЯ ФОРМЫ ЦЕНЫ ===
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        settings = SiteSettings.get_solo()
        extra_context['settings_form'] = PostcardSettingsForm(instance=settings)
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('update-settings/', self.admin_site.admin_view(self.update_settings_view),
                 name='update_postcard_settings'),
        ]
        return custom_urls + urls

    def update_settings_view(self, request):
        if request.method == 'POST':
            settings = SiteSettings.get_solo()
            form = PostcardSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                self.message_user(request, "Цена за 'Своё фото' обновлена!", messages.SUCCESS)
            else:
                self.message_user(request, "Ошибка сохранения.", messages.ERROR)
        return redirect('admin:shop_postcard_changelist')


@admin.register(Banner)
class BannerAdmin(SortableAdminMixin, ShopAdminStyleMixin, admin.ModelAdmin):
    form = BannerAdminForm
    change_list_template = "admin/shop/banner/change_list_slider.html"

    # 1. В list_display order ДОЛЖЕН быть
    list_display = ('get_title_display', 'image_preview', 'is_active', 'order')

    # 2. В list_display_links order НЕ ДОЛЖЕН быть
    list_display_links = ('get_title_display', 'image_preview')

    # 3. В list_editable order НЕ ДОЛЖЕН быть
    list_editable = ('is_active',)

    # 4. Важные настройки для сортировки
    ordering = ['order']
    sortable_by = []  # Отключаем сортировку по клику на заголовок
    search_fields = ('title', 'subtitle')

    # 5. Для sortable обязательно указать поле порядка
    list_per_page = 50  # Можно увеличить для лучшего drag-and-drop

    fieldsets = (
        ('Контент', {'fields': ('title', 'subtitle', 'button_text', 'link', 'content_position')}),
        ('Стилизация текста', {'fields': ('background_opacity', 'font_color', 'font_family')}),
        ('Изображение', {'fields': ('image', 'image_preview')}),
        ('Статус и порядок', {'fields': ('is_active',)}),
    )
    readonly_fields = ('image_preview',)

    def get_title_display(self, obj):
        if obj.title: return obj.title
        return format_html('<span style="color: #999; font-style: italic;">(Без заголовка)</span>')

    get_title_display.short_description = "Заголовок"
    get_title_display.admin_order_field = 'title'

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="150" style="border-radius: 4px; object-fit: cover; height: 60px;" />',
                obj.image.url)
        return "Нет фото"

    image_preview.short_description = 'Превью'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['image'].label = "Изображение"
        form.base_fields['image'].help_text = "В режиме Адаптивно растянутся по большей высоте (если они разные)."
        return form


    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            settings = SiteSettings.get_solo()
            extra_context['slider_form'] = SliderSettingsForm(instance=settings)
        except:
            pass
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('update-slider/', self.admin_site.admin_view(self.update_slider_view), name='update_slider_settings'),

        ]
        return custom_urls + urls

    def update_slider_view(self, request):
        if request.method == 'POST':
            settings = SiteSettings.get_solo()
            form = SliderSettingsForm(request.POST, instance=settings)
            if form.is_valid():
                form.save()
                self.message_user(request, "✅ Настройки слайдера успешно сохранены!", messages.SUCCESS)
            else:
                self.message_user(request, "❌ Ошибка при сохранении настроек.", messages.ERROR)
        return redirect('admin:shop_banner_changelist')


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, ShopAdminStyleMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    list_display_links = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'image_preview', 'alt_text')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image_thumbnail:
            return format_html('<img src="{}" />', obj.image_thumbnail.url)
        return "Нет фото"

    image_preview.short_description = 'Превью'


@admin.register(Product)
class ProductAdmin(ShopAdminStyleMixin, admin.ModelAdmin):
    # У товаров НЕТ сортировки, поэтому SortableAdminMixin не нужен
    form = ProductAdminForm
    list_display = ['sku', 'name', 'price', 'old_price', 'stock', 'available', 'is_featured', 'discount_colors_preview']
    list_filter = ['available', 'is_featured', 'created', 'updated']
    list_editable = ['price', 'old_price', 'stock', 'available', 'is_featured']
    list_display_links = ['sku', 'name']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug', 'sku']
    filter_horizontal = ('category',)

    fieldsets = (
        (None, {'fields': ('name', 'slug', 'sku', 'category')}),
        ('Основное изображение', {'fields': ('image', 'image_preview_detail')}),
        ('Блок "Состав"', {'fields': ('composition_title', 'composition')}),
        ('Блок "Описание"', {'fields': ('description_title', 'description')}),
        ('Цена и наличие', {'fields': ('price', 'old_price', 'stock')}),
        ('Настройки цветов скидки', {
            'fields': (
                ('discount_sticker_color', 'new_price_color'),
            ),
            'description': 'Настройка цветов отображения скидки на сайте.'
        }),
        ('Статус', {'fields': ('available', 'is_featured')}),
    )

    readonly_fields = ('image_preview_detail',)
    inlines = [ProductImageInline]

    def image_preview_detail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" />', obj.image.url)
        return "Нет фото"

    image_preview_detail.short_description = 'Превью основного изображения'

    def discount_colors_preview(self, obj):
        if not obj.old_price or obj.old_price <= obj.price:
            return "-"
        sticker_color = obj.get_discount_sticker_color()
        new_price_color = obj.get_new_price_color()
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<div title="Цвет стикера" style="width: 20px; height: 20px; background-color: {}; border-radius: 50%; border: 1px solid #ddd;"></div>'
            '<div title="Цвет новой цены" style="width: 20px; height: 20px; background-color: {}; border-radius: 50%; border: 1px solid #ddd;"></div>'
            '</div>', sticker_color, new_price_color
        )

    discount_colors_preview.short_description = 'Цвета скидки'


@admin.register(FooterPage)
class FooterPageAdmin(SortableAdminMixin, ShopAdminStyleMixin, admin.ModelAdmin):
    list_display = ('title', 'slug', 'order')
    list_display_links = ('title',)
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('special_page_warning',)

    fieldsets = (
        (None, {'fields': ('title', 'slug', 'special_page_warning')}),
        ('Контент', {'fields': ('page_title', 'content')}),
        #('Настройки', {'fields': ('order',)}),
    )

    def special_page_warning(self, obj):
        # Показываем подсказку всегда, чтобы админ знал, какие слаги использовать
        hint = (
            '<div style="background-color: #6e8091; border: 1px solid #b3d7ff; color: #004085; padding: 12px; border-radius: 5px; margin-bottom: 10px;">'
            '<strong>💡 Подсказка:</strong> Для подключения специальных шаблонов используйте следующие URL-адреса:'
            '<ul style="margin: 5px 0 0 20px; padding: 0;">'
            '<li><code>contacts</code> — Страница "Контакты" (берет данные из настроек сайта)</li>'
            '<li><code>about</code> — О нас</li>'
            '<li><code>payment</code> — Оплата и доставка</li>'
            '<li><code>terms</code> — Договор оферты</li>'
            '</ul>'
            '</div>'
        )

        if obj:
            if obj.slug == 'contacts':
                return format_html(
                    hint + '<div style="color: red; font-weight: bold; margin-top: 5px;">⚠️ ВНИМАНИЕ: Контент этой страницы берется из "Настроек сайта"!</div>')
            elif obj.slug in ['about', 'payment', 'terms']:
                return format_html(
                    hint + f'<div style="color: green; font-weight: bold; margin-top: 5px;">✔ Используется шаблон: {obj.slug}.html</div>')

        return format_html(hint)

    special_page_warning.short_description = "Статус шаблона"


@admin.register(Benefit)
class BenefitAdmin(SortableAdminMixin, ShopAdminStyleMixin, admin.ModelAdmin):
    list_display = ('title', 'icon_preview', 'is_active', 'order')
    list_display_links = ('title', 'icon_preview')
    list_editable = ('is_active',)
    fieldsets = (
        (None, {'fields': ('title', 'description', 'is_active')}),
        ('Иконка', {'fields': ('icon_svg', 'icon_preview'), 'description': 'Вставьте SVG код иконки.'}),
    )
    readonly_fields = ('icon_preview',)

    def icon_preview(self, obj):
        if obj.icon_svg:
            return format_html('<div style="width: 30px; height: 30px; color: #333;">{}</div>', mark_safe(obj.icon_svg))
        return "-"

    icon_preview.short_description = "Иконка"


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdmin):
    form = SiteSettingsForm
    save_on_top = True

    @property
    def media(self):
        media = super().media
        css = {'all': ('shop/css/admin_custom_buttons.css',)}
        js = ('shop/js/admin_scripts.js', 'shop/js/admin_timezone.js',)
        return media + forms.Media(css=css, js=js)

    readonly_fields = (
    'timezone_preview', 'apply_sku_logic_button', 'apply_order_logic_button', 'image_preview', 'discount_colors_info')

    fieldsets = (
        ('Основные настройки', {
            'classes': ('collapse',),
            'fields': (
                ('site_time_zone', 'timezone_preview'),
                ('shop_name', 'logo_image'),
                'image_preview',
                'sku_start_number',
                'apply_sku_logic_button',
                'order_start_number',
                'apply_order_logic_button',
                ('contact_phone', 'contact_phone_secondary'),
                'contact_email',
                ('pickup_address', 'working_hours'),
                'map_embed_code',
                ('contacts_page_title', 'contacts_address_title', 'contacts_hours_title', 'contacts_phone_title'),
                'admin_notification_emails',
                'delivery_cost', 'background_image',
                ('site_sheet_bg_color', 'site_sheet_opacity', 'site_sheet_blur'),
            )
        }),
        ('Время работы и Интервалы', {
            'classes': ('collapse',),
            'fields': (
                ('work_weekdays_open', 'work_weekdays_close'),
                ('work_weekend_open', 'work_weekend_close'),
                ('delivery_weekdays_open', 'delivery_weekdays_close'),
                ('delivery_weekend_open', 'delivery_weekend_close'),
                ('processing_time', 'close_cutoff', 'interval_step'),
            ),
            'description': 'Настройки времени открытия/закрытия для генерации интервалов доставки.'
        }),
        ('Цвета скидок (глобальные)', {
            'classes': ('collapse',),
            'fields': (
                'discount_colors_info',
                ('default_discount_sticker_color', 'default_new_price_color'),
            )
        }),
        ('Глобальное оформление (Меню и Шрифты)', {
            'classes': ('collapse',),
            'fields': (
                ('icon_size', 'icon_color', 'icon_animation_style'),
                ('default_font_family', 'default_font_size', 'default_text_color'),
                ('heading_font_family', 'heading_font_size', 'heading_font_style', 'accent_color'),
                ('logo_font_family', 'logo_font_size', 'logo_font_style', 'logo_color'),
                ('category_font_family', 'category_font_size', 'category_font_style', 'category_text_color'),
                ('footer_font_family', 'footer_font_size', 'footer_font_style', 'footer_text_color'),
                ('product_title_font_family', 'product_title_font_size', 'product_title_font_style',
                 'product_title_text_color'),
                ('product_header_font_family', 'product_header_font_size', 'product_header_font_style',
                 'product_header_text_color'),
                'navigation_style',
            )
        }),
        ('Настройки поведения шапки', {
            'classes': ('collapse',),
            'fields': (
                'desktop_header_behavior',
                ('desktop_header_scroll_enabled', 'desktop_header_scroll_opacity', 'desktop_header_blur'),
                ('desktop_category_scroll_enabled', 'desktop_categories_opacity', 'desktop_category_blur'),
                ('desktop_categories_bg_mode', 'desktop_categories_bg_color'),
                'mobile_header_behavior',
                ('mobile_header_transparent_scroll', 'mobile_header_scroll_opacity', 'mobile_header_blur'),
                ('mobile_header_bg_mode', 'mobile_header_bg_color_custom'),
            )
        }),
        ('Настройки каталога', {
            'classes': ('collapse',),
            'fields': (
                'all_products_text',
                ('catalog_title', 'catalog_title_color'),
                ('catalog_title_font_family', 'catalog_title_font_style'),
                ('popular_title', 'popular_title_color'),
                ('popular_title_font_family', 'popular_title_font_style'),
                'default_composition_title', 'default_description_title'
            )
        }),
        ('Тонкие настройки кнопок', {
            'classes': ('collapse',),
            'fields': (
                'button_style_preset',
                ('button_bg_color', 'button_accent_color'),
                ('button_text_color', 'button_hover_bg_color'),
                ('add_to_cart_bg_color', 'add_to_cart_text_color', 'add_to_cart_hover_bg_color'),
                'button_border_radius',
                ('button_font_family', 'button_font_style'),
            )
        }),
        ('Настройки мобильной версии', {
            'classes': ('collapse',),
            'fields': (
                'mobile_header_style', 'mobile_font_scale',
                'mobile_product_grid',
                'collapse_categories_threshold', 'collapse_footer_threshold',
            )
        }),
        ('Мобильное меню', {
            'classes': ('collapse',),
            'fields': (
                'mobile_button_override_global',
                'mobile_dropdown_view_mode',
                ('mobile_dropdown_bg_color', 'mobile_dropdown_opacity'),
                'mobile_dropdown_font_color',
                ('mobile_dropdown_font_family', 'mobile_dropdown_font_size', 'mobile_dropdown_font_style'),
                'mobile_dropdown_button_bg_color',
                'mobile_dropdown_button_text_color',
                ('mobile_dropdown_inherit_radius', 'mobile_dropdown_button_border_radius'),
                'mobile_dropdown_button_opacity',
            )
        }),
        ('Статичные страницы', {
            'classes': ('collapse',),
            'fields': (
                'static_page_title_color',
                'static_page_subtitle_color',
                'static_page_icon_color',
                'static_page_link_color',
                'static_page_link_hover_color',
            )
        }),
    )

    def timezone_preview(self, obj):
        return format_html(
            '<span id="timezone-clock-preview" style="font-size: 14px; padding-left: 10px; line-height: 35px;">Загрузка времени...</span>')

    timezone_preview.short_description = "Текущее время в регионе"

    def image_preview(self, obj):
        if obj.logo_image:
            return format_html('<img src="{}" width="150" />', obj.logo_image.url)
        return "Логотип не загружен"

    image_preview.short_description = "Превью логотипа"

    def discount_colors_info(self, obj):
        return format_html(
            '<div style="background-color: #363a36; border-left: 4px solid #e53935; padding: 10px 15px; margin-bottom: 15px;">...</div>')

    discount_colors_info.short_description = "Информация"

    def save_model(self, request, obj, form, change):
        if obj.mobile_font_scale is not None:
            if obj.mobile_font_scale > 50 or obj.mobile_font_scale < -50:
                obj.mobile_font_scale = 0
        super().save_model(request, obj, form, change)
        if '_run_sku_script' in request.POST:
            out = StringIO()
            call_command('fix_skus', stdout=out)
            self.message_user(request, "Настройки сохранены. Артикулы обновлены!", level='success')
        if '_run_order_script' in request.POST:
            out = StringIO()
            call_command('fix_order_ids', stdout=out)
            self.message_user(request, "Настройки сохранены. Заказы перенумерованы!", level='success')

    def apply_sku_logic_button(self, obj):
        return format_html(
            '<button type="submit" name="_run_sku_script" value="1" style="background:#28a745; color:white; border:none; padding:8px 15px; border-radius:4px; cursor:pointer;">💾 Сохранить и Обновить артикулы</button>')

    apply_sku_logic_button.short_description = "Действие"

    def apply_order_logic_button(self, obj):
        return format_html(
            '<button type="submit" name="_run_order_script" value="1" style="background:#dc3545; color:white; border:none; padding:8px 15px; border-radius:4px; cursor:pointer;">💾 Сохранить и Перенумеровать заказы</button>')

    apply_order_logic_button.short_description = "Действие"

    def download_backup_view(self, request):
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, 'backup.dump')
        db = settings.DATABASES['default']
        if 'sqlite3' in db['ENGINE']:
            return FileResponse(open(db['NAME'], 'rb'), as_attachment=True, filename='db.sqlite3')
        command = ['pg_dump', '-U', db.get('USER'), '-h', db.get('HOST', 'localhost'), '-p', str(db.get('PORT', 5432)),
                   '--format=custom', '-f', backup_path, db.get('NAME')]
        env = os.environ.copy()
        if db.get('PASSWORD'): env['PGPASSWORD'] = db['PASSWORD']
        try:
            subprocess.run(command, env=env, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.message_user(request, f"Ошибка: {e}", level='error')
            return redirect('admin:shop_sitesettings_change', 1)
        return FileResponse(open(backup_path, 'rb'), as_attachment=True, filename='megacvet_backup_db.dump')

    def download_media_view(self, request):
        media_root = settings.MEDIA_ROOT
        buffer = io.BytesIO()
        try:
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        zip_file.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), media_root))
            buffer.seek(0)
            return FileResponse(buffer, as_attachment=True, filename="megacvet_backup_media.zip")
        except Exception as e:
            self.message_user(request, f"Ошибка: {e}", level='error')
            return redirect('admin:shop_sitesettings_change', 1)

    def download_env_view(self, request):
        env_path = os.path.join(settings.BASE_DIR, '.env')
        if os.path.exists(env_path):
            return FileResponse(open(env_path, 'rb'), as_attachment=True, filename='.env')
        else:
            self.message_user(request, ".env не найден", level='error')
            return redirect('admin:shop_sitesettings_change', 1)

    def download_config_view(self, request):
        config_path = os.path.join(settings.BASE_DIR, 'ecosystem.config.js')
        if os.path.exists(config_path):
            return FileResponse(open(config_path, 'rb'), as_attachment=True, filename='ecosystem.config.js')
        else:
            self.message_user(request, "Файл не найден", level='warning')
            return redirect('admin:shop_sitesettings_change', 1)