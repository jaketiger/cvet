# shop/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, Product, Profile, SiteSettings, FooterPage, ProductImage, Banner, Benefit, Postcard
from solo.admin import SingletonModelAdmin
from adminsortable2.admin import SortableAdminMixin
from django.utils.html import format_html
from django.urls import path, reverse
import subprocess
import os
import zipfile
import io
from django.conf import settings
from django.http import FileResponse
from django.shortcuts import redirect
from .forms import SiteSettingsForm, BannerAdminForm
from django.utils.safestring import mark_safe


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Дополнительные поля профиля'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Postcard)
class PostcardAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'preview', 'price', 'is_active', 'order')
    list_editable = ('price', 'is_active', 'order')
    list_filter = ('is_active',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height: 50px; border-radius: 4px;" />', obj.image.url)
        return "-"

    preview.short_description = "Фото"

@admin.register(Banner)
class BannerAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = BannerAdminForm
    list_display = ('title', 'image_preview', 'is_active', 'order')
    list_editable = ('is_active',)
    search_fields = ('title', 'subtitle')
    fieldsets = (
        ('Контент', {'fields': ('title', 'subtitle', 'button_text', 'link', 'content_position')}),
        ('Стилизация текста', {'fields': ('background_opacity', 'font_color', 'font_family')}),
        ('Изображение', {'fields': ('image', 'image_preview')}),
        ('Статус и порядок', {'fields': ('is_active',)}),
    )
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image: return format_html('<img src="{}" width="200" />', obj.image.url)
        return "Нет фото"

    image_preview.short_description = 'Превью'


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'image_preview', 'alt_text')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image_thumbnail: return format_html('<img src="{}" />', obj.image_thumbnail.url)
        return "Нет фото"

    image_preview.short_description = 'Превью'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'stock', 'available', 'is_featured']
    list_filter = ['available', 'is_featured', 'created', 'updated']
    list_editable = ['price', 'stock', 'available', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']
    filter_horizontal = ('category',)
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'category')}),
        ('Основное изображение', {'fields': ('image', 'image_preview_detail')}),
        ('Блок "Состав" (под фото)', {'fields': ('composition_title', 'composition')}),
        ('Блок "Описание" (справа от фото)', {'fields': ('description_title', 'description')}),
        ('Цена и наличие', {'fields': ('price', 'stock')}),
        ('Статус', {'fields': ('available', 'is_featured')}),
    )
    readonly_fields = ('image_preview_detail',)
    inlines = [ProductImageInline]

    def image_preview_list(self, obj):
        if obj.image_thumbnail: return format_html('<img src="{}" width="50" />', obj.image_thumbnail.url)
        return "Нет фото"

    image_preview_list.short_description = 'Фото'

    def image_preview_detail(self, obj):
        if obj.image: return format_html('<img src="{}" width="200" />', obj.image.url)
        return "Нет фото"

    image_preview_detail.short_description = 'Превью основного изображения'

    def category_list(self, obj):
        return ", ".join([c.name for c in obj.category.all()])

    category_list.short_description = 'Категории'


@admin.register(FooterPage)
class FooterPageAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'slug', 'order')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Benefit)
class BenefitAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'icon_preview', 'is_active', 'order')
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

    fieldsets = (
        ('Основные настройки', {
            'classes': ('collapse',),
            'description': "Ключевая информация о вашем магазине.",
            'fields': (
                'shop_name',
                ('contact_phone', 'contact_phone_secondary'),
                ('pickup_address', 'working_hours'),
                'map_embed_code',
                ('contacts_page_title', 'contacts_address_title', 'contacts_hours_title', 'contacts_phone_title'),
                'admin_notification_emails',
                'delivery_cost', 'background_image',
                ('site_sheet_bg_color', 'site_sheet_opacity', 'site_sheet_blur'),
            )
        }),

        # --- ГРУППА: РЕДАКТИРОВАНИЕ КАРТОЧКИ ТОВАРА ---
        # ЭТОТ БЛОК УДАЛЕН ИЗ-ЗА УДАЛЕНИЯ ПОЛЕЙ ИЗ МОДЕЛИ
        # ('Редактирование карточки товара (Фото и Кнопки)', {
        #     'classes': ('collapse',),
        #     'description': "Настройки отображения фото и элементов управления.",
        #     'fields': (
        #         'product_image_zoom_factor',
        #         'product_button_size',
        #     )
        # }),
        # -----------------------------------------------

        ('Настройки поведения шапки (Header)', {
            'classes': ('collapse',),
            'description': "Управление фиксацией, прозрачностью и фоном.",
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
        ('Настройки каталога и товара (Тексты)', {
            'classes': ('collapse',),
            'description': "Заголовки страниц каталога.",
            'fields': (
                'all_products_text',
                ('catalog_title', 'catalog_title_color'),
                ('catalog_title_font_family', 'catalog_title_font_style'),
                ('popular_title', 'popular_title_color'),
                ('popular_title_font_family', 'popular_title_font_style'),
                'default_composition_title', 'default_description_title'
            )
        }),
        ('Настройки слайдера (баннеров)', {
            'classes': ('collapse',),
            'fields': (
                ('slider_duration', 'slider_effect'),
            )
        }),
        ('Глобальное оформление сайта', {
            'classes': ('collapse',),
            'description': "Шрифты и цвета всего сайта.",
            'fields': (
                ('default_font_family', 'default_font_size', 'default_text_color'),
                ('heading_font_family', 'heading_font_size', 'heading_font_style', 'accent_color'),
                ('logo_font_family', 'logo_font_size', 'logo_font_style', 'logo_color'),
                ('icon_size', 'icon_color', 'icon_animation_style'),
                ('category_font_family', 'category_font_size', 'category_font_style', 'category_text_color'),
                ('footer_font_family', 'footer_font_size', 'footer_font_style', 'footer_text_color'),
                ('product_title_font_family', 'product_title_font_size', 'product_title_font_style',
                 'product_title_text_color'),
                ('product_header_font_family', 'product_header_font_size', 'product_header_font_style',
                 'product_header_text_color'),
                'navigation_style',
            )
        }),
        ('Тонкие настройки: Кнопок', {
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
        ('Настройки выпадающих меню (моб. версия)', {
            'classes': ('collapse',),
            'fields': (
                'mobile_button_override_global',
                'mobile_dropdown_view_mode',
                ('mobile_dropdown_bg_color', 'mobile_dropdown_opacity'),
                'mobile_dropdown_font_color',
                ('mobile_dropdown_font_family', 'mobile_dropdown_font_size', 'mobile_dropdown_font_style'),
                'mobile_dropdown_button_bg_color',
                'mobile_dropdown_button_text_color',
                ('mobile_dropdown_button_border_radius', 'mobile_dropdown_button_opacity'),
            )
        }),
        ('Стилизация статичных страниц', {
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

    change_form_template = "admin/shop/sitesettings/change_form.html"

    def save_model(self, request, obj, form, change):
        if obj.mobile_font_scale is not None:
            if obj.mobile_font_scale > 50 or obj.mobile_font_scale < -50:
                obj.mobile_font_scale = 0
        super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('backup/db/', self.admin_site.admin_view(self.download_backup_view), name='site_backup_db'),
            path('backup/media/', self.admin_site.admin_view(self.download_media_view), name='site_backup_media'),
            path('backup/env/', self.admin_site.admin_view(self.download_env_view), name='site_backup_env'),
            path('backup/config/', self.admin_site.admin_view(self.download_config_view), name='site_backup_config'),
        ]
        return custom_urls + urls

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['media_root_path'] = settings.MEDIA_ROOT
        return super().change_view(request, object_id, form_url, extra_context=extra_context)

    def download_backup_view(self, request):
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, 'backup.dump')
        db = settings.DATABASES['default']
        command = ['pg_dump', '-U', db.get('USER'), '-h', db.get('HOST', 'localhost'), '-p', str(db.get('PORT', 5432)),
                   '--format=custom', '-f', backup_path, db.get('NAME')]
        env = os.environ.copy()
        if db.get('PASSWORD'): env['PGPASSWORD'] = db['PASSWORD']
        try:
            subprocess.run(command, env=env, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.message_user(request, f"Ошибка создания бэкапа: {e}", level='error')
            return redirect(reverse('admin:shop_sitesettings_change', args=[SiteSettings.objects.get().pk]))
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
            self.message_user(request, f"Ошибка архивации media: {e}", level='error')
            return redirect(reverse('admin:shop_sitesettings_change', args=[SiteSettings.objects.get().pk]))

    def download_env_view(self, request):
        env_path = os.path.join(settings.BASE_DIR, '.env')
        if os.path.exists(env_path):
            return FileResponse(open(env_path, 'rb'), as_attachment=True, filename='.env')
        else:
            self.message_user(request, "Файл .env не найден.", level='error')
            return redirect(reverse('admin:shop_sitesettings_change', args=[SiteSettings.objects.get().pk]))

    def download_config_view(self, request):
        config_path = os.path.join(settings.BASE_DIR, 'ecosystem.config.js')
        if os.path.exists(config_path):
            return FileResponse(open(config_path, 'rb'), as_attachment=True, filename='ecosystem.config.js')
        else:
            self.message_user(request, "Файл ecosystem.config.js не найден.", level='warning')
            return redirect(reverse('admin:shop_sitesettings_change', args=[SiteSettings.objects.get().pk]))