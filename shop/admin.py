# shop/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, Product, Profile, SiteSettings, FooterPage, ProductImage, Banner
from solo.admin import SingletonModelAdmin
from adminsortable2.admin import SortableAdminMixin
from django.utils.html import format_html
from django.urls import path, reverse
import subprocess, os
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

    def image_preview(self, obj):
        if obj.image: return format_html('<img src="{}" width="200" />', obj.image.url)
        return "Нет фото"

    image_preview.short_description = 'Превью'
    list_display = ('title', 'image_preview', 'is_active', 'order')
    list_editable = ('is_active',)
    search_fields = ('title', 'subtitle')
    fieldsets = (('Контент', {'fields': ('title', 'subtitle', 'button_text', 'link', 'content_position')}),
                 ('Стилизация текста', {'fields': ('background_opacity', 'font_color', 'font_family')}),
                 ('Изображение', {'fields': ('image', 'image_preview')}),
                 ('Статус и порядок', {'fields': ('is_active',)}),)
    readonly_fields = ('image_preview',)


@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

    def image_preview(self, obj):
        if obj.image_thumbnail: return format_html('<img src="{}" />', obj.image_thumbnail.url)
        return "Нет фото"

    image_preview.short_description = 'Превью'
    fields = ('image', 'image_preview', 'alt_text')
    readonly_fields = ('image_preview',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    def image_preview_list(self, obj):
        if obj.image_thumbnail: return format_html('<img src="{}" width="50" />', obj.image_thumbnail.url)
        return "Нет фото"

    image_preview_list.short_description = 'Фото'

    def image_preview_detail(self, obj):
        if obj.image: return format_html('<img src="{}" width="200" />', obj.image.url)
        return "Нет фото"

    image_preview_detail.short_description = 'Превью основного изображения'

    list_display = ['name', 'slug', 'image_preview_list', 'category_list', 'price', 'stock', 'available', 'is_featured']
    list_filter = ['available', 'is_featured', 'created', 'updated']
    list_editable = ['price', 'stock', 'available', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']
    filter_horizontal = ('category',)

    fieldsets = (
        (None, {'fields': ('name', 'slug', 'category')}),
        ('Основное изображение', {'fields': ('image', 'image_preview_detail')}),
        ('Состав (блок под фото)', {'fields': ('composition_title', 'composition')}),
        ('Описание (блок справа от фото)', {'fields': ('description_title', 'description')}),
        ('Цена и наличие', {'fields': ('price', 'stock')}),
        ('Статус', {'fields': ('available', 'is_featured')}),
    )

    readonly_fields = ('image_preview_detail',)
    inlines = [ProductImageInline]

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

    # ▼▼▼ ВОССТАНОВЛЕННЫЙ БЛОК fieldsets ▼▼▼
    fieldsets = (
        ('Настройки мобильной версии', {
            'description': 'Здесь настраивается внешний вид сайта на смартфонах и планшетах.',
            'fields': (
                'mobile_header_style',
                'mobile_product_grid',
                'collapse_categories_threshold',
                'collapse_footer_threshold',
            )
        }),
        ('Основные настройки',
         {'fields': ('shop_name', 'contact_phone', 'admin_notification_emails', 'delivery_cost', 'background_image')}),

        ('Глобальное оформление сайта', {
            'classes': ('collapse',),
            'fields': (
                'navigation_style',
                ('main_text_color', 'accent_color'),
                ('body_font_family', 'heading_font_family'),
                'base_font_size'
            )
        }),

        ('Тонкие настройки: Шапка (Логотип)', {
            'classes': ('collapse',),
            'fields': ('logo_color', 'logo_font_size', 'logo_font_family')
        }),
        ('Тонкие настройки: Меню категорий', {
            'classes': ('collapse',),
            'fields': ('category_nav_font_family', 'category_nav_font_size',
                       ('category_nav_font_color', 'category_nav_hover_color'))
        }),
        ('Тонкие настройки: Карточка товара', {
            'classes': ('collapse',),
            'fields': ('product_card_title_font_family', 'product_card_title_font_size',
                       ('product_card_title_color', 'product_card_price_color'))
        }),
        ('Тонкие настройки: Футер', {
            'classes': ('collapse',),
            'fields': ('footer_font_size', 'footer_font_color')
        }),

        ('Тонкие настройки: Кнопки', {
            'classes': ('collapse',),
            'description': """
                <p>Здесь настраивается внешний вид кнопок на сайте.</p>
                <p><b>Общие настройки</b> применяются ко всем кнопкам, если для них не задан уникальный стиль.</p>
                <p><b>Настройки для кнопки "В корзину"</b> имеют приоритет и позволяют задать для нее уникальный цвет.</p>
            """,
            'fields': (
                ('button_bg_color', 'button_text_color'),
                'button_hover_bg_color',
                'add_to_cart_bg_color',
                'add_to_cart_text_color',
                'add_to_cart_hover_bg_color',
                'button_border_radius',
                'button_font_family',
            )
        }),

        ('Настройки слайдера', {'fields': (('slider_duration', 'slider_effect'),)}),
        ('Заголовки по умолчанию для страницы товара', {
            'fields': ('default_composition_title', 'default_description_title')
        }),
    )

    # ▼▼▼ ВОССТАНОВЛЕННЫЕ МЕТОДЫ ДЛЯ КАСТОМНЫХ КНОПОК ▼▼▼
    change_form_template = "admin/shop/sitesettings/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [path('backup/download/', self.admin_site.admin_view(self.download_backup_view),
                            name='site_backup_download')]
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
            error_message = f"Ошибка создания бэкапа: {e}"
            if isinstance(e, subprocess.CalledProcessError): error_message += f" | {e.stderr}"
            self.message_user(request, error_message, level='error')
            return redirect(reverse('admin:shop_sitesettings_change', args=[SiteSettings.objects.get().pk]))
        return FileResponse(open(backup_path, 'rb'), as_attachment=True, filename='megacvet_backup.dump')