# shop/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, Product, Profile, SiteSettings, FooterPage, ProductImage, Banner
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


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Дополнительные поля профиля'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Banner)
class BannerAdmin(SortableAdminMixin, admin.ModelAdmin):
    form = BannerAdminForm
    list_display = ('title', 'image_preview', 'is_active', 'order')
    list_editable = ('is_active',)
    search_fields = ('title', 'subtitle')
    fieldsets = (('Контент', {'fields': ('title', 'subtitle', 'button_text', 'link', 'content_position')}),
                 ('Стилизация текста', {'fields': ('background_opacity', 'font_color', 'font_family')}),
                 ('Изображение', {'fields': ('image', 'image_preview')}),
                 ('Статус и порядок', {'fields': ('is_active',)}),)
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
    list_display = ['name', 'slug', 'image_preview_list', 'category_list', 'price', 'stock', 'available',
                    'is_featured']
    list_filter = ['available', 'is_featured', 'created', 'updated']
    list_editable = ['price', 'stock', 'available', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']
    filter_horizontal = ('category',)
    fieldsets = ((None, {'fields': ('name', 'slug', 'category')}),
                 ('Основное изображение', {'fields': ('image', 'image_preview_detail')}),
                 ('Блок "Состав" (под фото)', {'fields': ('composition_title', 'composition')}),
                 ('Блок "Описание" (справа от фото)', {'fields': ('description_title', 'description')}),
                 ('Цена и наличие', {'fields': ('price', 'stock')}),
                 ('Статус', {'fields': ('available', 'is_featured')}),)
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


@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdmin):
    form = SiteSettingsForm

    fieldsets = (
        ('Основные настройки', {
            'classes': ('collapse',),
            'description': "Ключевая информация о вашем магазине: название, контакты, email для уведомлений и стоимость доставки.",
            'fields': (
                'shop_name', 'contact_phone', 'admin_notification_emails',
                'delivery_cost', 'background_image'
            )
        }),
        ('Настройки каталога и товара', {
            'classes': ('collapse',),
            'description': "Тексты по умолчанию для элементов каталога и страниц товаров.",
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
            'description': "Управление поведением слайдера на главной странице.",
            'fields': (
                ('slider_duration', 'slider_effect'),
            )
        }),
        ('Глобальное оформление сайта', {
            'classes': ('collapse',),
            'description': "Здесь вы можете задать шрифты, размеры и цвета для основных элементов сайта.",
            'fields': (
                'default_font_family', 'default_font_size', 'default_text_color',
                'logo_font_family', 'logo_font_size', 'logo_font_style', 'logo_color',
                'icon_size', 'icon_color',
                'category_font_family', 'category_font_size', 'category_font_style', 'category_text_color',
                'footer_font_family', 'footer_font_size', 'footer_font_style', 'footer_text_color',
                'product_title_font_family', 'product_title_font_size', 'product_title_font_style',
                'product_title_text_color',
                'product_header_font_family', 'product_header_font_size', 'product_header_font_style',
                'product_header_text_color',
                'navigation_style',
                'icon_animation_style',
                'heading_font_family', 'heading_font_style',
                'accent_color',
            )
        }),
        ('Тонкие настройки: Кнопки', {
            'classes': ('collapse',),
            'description': "Кастомизация внешнего вида всех кнопок на сайте.",
            'fields': (
                'button_bg_color', 'button_text_color', 'button_hover_bg_color', 'add_to_cart_bg_color',
                'add_to_cart_text_color', 'add_to_cart_hover_bg_color', 'button_border_radius',
                'button_font_family', 'button_font_style',
            )
        }),
        ('Настройки мобильной версии', {
            'classes': ('collapse',),
            'description': "Все, что связано с отображением сайта на смартфонах и планшетах.",
            'fields': (
                'mobile_header_style', 'mobile_product_grid',
                'collapse_categories_threshold', 'collapse_footer_threshold',
            )
        }),
        ('Настройки выпадающих меню (моб. версия)', {
            'classes': ('collapse',),
            'description': "Стилизация всплывающих окон (поиск, корзина, кабинет, категории) в мобильной версии.",
            'fields': (
                'mobile_dropdown_view_mode',
                ('mobile_dropdown_bg_color', 'mobile_dropdown_opacity'),
                'mobile_dropdown_font_color',
                ('mobile_dropdown_font_family', 'mobile_dropdown_font_size', 'mobile_dropdown_font_style'),
                'mobile_dropdown_button_bg_color',
                'mobile_dropdown_button_text_color',
                ('mobile_dropdown_button_border_radius', 'mobile_dropdown_button_opacity'),
            )
        }),
    )

    change_form_template = "admin/shop/sitesettings/change_form.html"

    class Media:
        js = ('admin/js/custom_admin.js',)

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

    # 1. Скачивание БД
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
            error_message = f"Ошибка создания бэкапа: {e}"
            if isinstance(e, subprocess.CalledProcessError):
                error_message = f"{error_message} | {e.stderr}"
            self.message_user(request, error_message, level='error')
            return redirect(reverse('admin:shop_sitesettings_change', args=[SiteSettings.objects.get().pk]))

        return FileResponse(open(backup_path, 'rb'), as_attachment=True, filename='megacvet_backup_db.dump')

    # 2. Скачивание Media
    def download_media_view(self, request):
        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            self.message_user(request, "Папка media не найдена.", level='error')
            return redirect(reverse('admin:shop_sitesettings_change', args=[SiteSettings.objects.get().pk]))

        buffer = io.BytesIO()
        try:
            with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, dirs, files in os.walk(media_root):
                    for file in files:
                        file_path = os.path.join(root, file)
                        archive_path = os.path.relpath(file_path, media_root)
                        zip_file.write(file_path, archive_path)

            buffer.seek(0)
            return FileResponse(buffer, as_attachment=True, filename="megacvet_backup_media.zip")
        except Exception as e:
            self.message_user(request, f"Ошибка архивации media: {e}", level='error')
            return redirect(reverse('admin:shop_sitesettings_change', args=[SiteSettings.objects.get().pk]))

    # 3. Скачивание .env
    def download_env_view(self, request):
        env_path = os.path.join(settings.BASE_DIR, '.env')
        if os.path.exists(env_path):
            return FileResponse(open(env_path, 'rb'), as_attachment=True, filename='.env')
        else:
            self.message_user(request, "Файл .env не найден в корне проекта.", level='error')
            return redirect(reverse('admin:shop_sitesettings_change', args=[SiteSettings.objects.get().pk]))

    # 4. Скачивание Config
    def download_config_view(self, request):
        config_path = os.path.join(settings.BASE_DIR, 'ecosystem.config.js')
        if os.path.exists(config_path):
            return FileResponse(open(config_path, 'rb'), as_attachment=True, filename='ecosystem.config.js')
        else:
            self.message_user(request, "Файл ecosystem.config.js не найден.", level='warning')
            return redirect(reverse('admin:shop_sitesettings_change', args=[SiteSettings.objects.get().pk]))