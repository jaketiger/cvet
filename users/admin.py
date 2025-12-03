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
    # 1. ВКЛЮЧАЕМ КНОПКИ СВЕРХУ
    # Эта настройка заставляет Django добавить панель "Сохранить" над формой.
    # Нижняя панель тоже добавляется, но мы скрываем её через CSS.
    save_on_top = True

    # 2. ШАБЛОН ДЛЯ СПИСКА
    # Подключаем шаблон, который добавляет кнопку "Сохранить" над ТАБЛИЦЕЙ (списком).
    # Используем универсальный шаблон без лишних кнопок.
    change_list_template = "admin/change_list_save_top.html"

    # 3. ПОДКЛЮЧАЕМ СТИЛИ
    # Этот CSS делает кнопки красивыми и СКРЫВАЕТ нижние дубликаты.
    class Media:
        css = {
            'all': ('shop/css/admin_custom_buttons.css',)
        }

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