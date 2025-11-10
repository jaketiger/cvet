# shop/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Category, Product, Profile, SiteSettings
from solo.admin import SingletonModelAdmin


# 1. Профиль в Пользователе
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Дополнительные поля профиля'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# --- 2. Улучшенный inline для Товаров в Категории ---
class ProductInline(admin.TabularInline):
    model = Product.category.through  # <-- Используем "промежуточную" таблицу для ManyToMany
    verbose_name = "Товар"
    verbose_name_plural = "Товары в этой категории"

    # --- ЭТА СТРОКА ЗАПРЕЩАЕТ СОЗДАНИЕ НОВЫХ ОБЪЕКТОВ ---
    # extra=0 убирает пустые слоты, can_delete=False убирает возможность удалить связь
    extra = 0
    can_delete = True

    # --- ВКЛЮЧАЕМ ПОИСК ДЛЯ ВЫБОРА СУЩЕСТВУЮЩИХ ТОВАРОВ ---
    autocomplete_fields = ['product']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']

    # --- ВОЗВРАЩАЕМ INLINE, НО В УЛУЧШЕННОМ ВИДЕ ---
    inlines = [ProductInline]

    # Мы не можем использовать filter_horizontal здесь, поэтому исключаем поле
    exclude = ('products',)


# 3. Улучшенная админка для Товаров
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'price', 'stock', 'available', 'is_featured']
    list_filter = ['available', 'is_featured', 'created', 'updated']
    list_editable = ['price', 'stock', 'available', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']

    # Этот виджет позволяет удобно выбирать несколько категорий для товара.
    filter_horizontal = ('category',)


# 4. Настройки сайта
admin.site.register(SiteSettings, SingletonModelAdmin)