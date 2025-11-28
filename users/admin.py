# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile


# 1. Встраиваем Профиль (телефон, адрес) в карточку Пользователя
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Дополнительные данные (Телефон, Адрес)'
    fk_name = 'user'


# 2. Настраиваем кастомную админку для User
class CustomUserAdmin(UserAdmin):
    # Добавляем наш инлайн с профилем
    inlines = (ProfileInline,)

    # Колонки, которые видны в списке пользователей
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_phone', 'is_staff', 'date_joined')

    # Сортировка по дате регистрации (сначала новые)
    ordering = ('-date_joined',)

    # === ВАЖНО: НАСТРОЙКА ПОИСКА ===
    # profile__phone означает: "Искать в связанной таблице profile поле phone"
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__phone')

    # Функция для вывода телефона в колонку списка
    def get_phone(self, instance):
        if hasattr(instance, 'profile') and instance.profile.phone:
            return instance.profile.phone
        return "-"

    get_phone.short_description = 'Телефон'


# 3. Перерегистрация модели User
# Сначала отменяем стандартную регистрацию, потом регистрируем с нашими настройками
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)