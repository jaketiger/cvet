# shop/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, Product, Profile, SiteSettings, FooterPage
from solo.admin import SingletonModelAdmin
from adminsortable2.admin import SortableAdminMixin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import redirect
from django.http import FileResponse
import subprocess
import os
from django.conf import settings


# 1. Профиль в Пользователе
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Дополнительные поля профиля'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# 2. Админка для Категорий
@admin.register(Category)
class CategoryAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']


# 3. Админка для Товаров
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    def image_preview_list(self, obj):
        if obj.image_thumbnail:
            return format_html('<img src="{}" width="50" />', obj.image_thumbnail.url)
        return "Нет фото"

    image_preview_list.short_description = 'Фото'

    def image_preview_detail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="200" />', obj.image.url)
        return "Нет фото"

    image_preview_detail.short_description = 'Превью изображения'

    list_display = ['name', 'slug', 'image_preview_list', 'category_list', 'price', 'stock', 'available', 'is_featured']
    list_filter = ['available', 'is_featured', 'created', 'updated']
    list_editable = ['price', 'stock', 'available', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']
    filter_horizontal = ('category',)

    fieldsets = (
        (None, {'fields': ('name', 'slug', 'category')}),
        ('Изображение', {'fields': ('image', 'image_preview_detail')}),
        ('Описание и цена', {'fields': ('description', 'price', 'stock')}),
        ('Статус', {'fields': ('available', 'is_featured')}),
    )
    readonly_fields = ('image_preview_detail',)

    def category_list(self, obj):
        return ", ".join([c.name for c in obj.category.all()])

    category_list.short_description = 'Категории'


# 4. Админка для страниц в футере
@admin.register(FooterPage)
class FooterPageAdmin(SortableAdminMixin, admin.ModelAdmin):
    list_display = ('title', 'slug', 'order')
    prepopulated_fields = {'slug': ('title',)}


# --- 5. ОБНОВЛЕННАЯ АДМИНКА ДЛЯ НАСТРОЕК САЙТА С КНОПКОЙ БЭКАПА ---

@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdmin):
    change_form_template = "admin/shop/sitesettings/change_form.html"

# admin.site.register(SiteSettings, SiteSettingsAdmin)



    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('backup/', self.admin_site.admin_view(self.backup_view), name='site_backup')
        ]
        return custom_urls + urls

    def backup_view(self, request):
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, 'backup.dump')

        db = settings.DATABASES['default']

        command = [
            'pg_dump',
            '-U', db.get('USER'),
            '-h', db.get('HOST', 'localhost'),
            '-p', str(db.get('PORT', 5432)),
            '--format=custom',
            '-f', backup_path,
            db.get('NAME')
        ]

        env = os.environ.copy()
        if db.get('PASSWORD'):
            env['PGPASSWORD'] = db['PASSWORD']

        try:
            subprocess.run(command, env=env, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            error_message = f"Ошибка создания бэкапа: {e}"
            if isinstance(e, subprocess.CalledProcessError):
                error_message += f" | {e.stderr}"
            self.message_user(request, error_message, level='error')
            return redirect("..")

        return FileResponse(open(backup_path, 'rb'), as_attachment=True, filename='megacvet_backup.dump')