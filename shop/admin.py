# shop/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import SiteSettings
from solo.admin import SingletonModelAdmin

# Импортируем все наши модели из shop/models.py
from .models import Category, Product, Profile


# --- 1. Встраиваем редактирование профиля в страницу пользователя ---

class ProfileInline(admin.StackedInline):
    """
    Определяет встраиваемую модель Profile для отображения
    внутри модели User.
    """
    model = Profile
    can_delete = False  # Нельзя удалить профиль со страницы пользователя
    verbose_name_plural = 'Дополнительные поля профиля'


class UserAdmin(BaseUserAdmin):
    """

    Расширяет стандартный UserAdmin, добавляя в него
    редактирование профиля.
    """
    inlines = (ProfileInline,)


# --- 2. Перерегистрируем стандартную модель User ---

# Сначала "открепляем" стандартную регистрацию User
admin.site.unregister(User)
# Затем "прикрепляем" нашу расширенную версию
admin.site.register(User, UserAdmin)


# --- 3. Ваш существующий код для Category и Product (он остается без изменений) ---

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'stock', 'available', 'created']
    list_filter = ['available', 'created', 'updated', 'category']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(SiteSettings, SingletonModelAdmin)