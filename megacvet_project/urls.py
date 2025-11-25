# megacvet_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from users.forms import LoginForm
from users import views as user_views

urlpatterns = [
    # 1. Админ-панель
    path('admin/', admin.site.urls),

    # 2. Аутентификация (вход, выход, сброс пароля)
    path('accounts/login/',
         auth_views.LoginView.as_view(template_name='registration/login.html', authentication_form=LoginForm),
         name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    path('accounts/password_reset/', user_views.password_reset_request, name='password_reset'),
    path('accounts/password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('accounts/reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

    # 3. URL-адреса наших приложений
    # Эта строка подключает users/urls.py и видит 'app_name = users'
    path('accounts/', include('users.urls')),

    path('cart/', include('cart.urls', namespace='cart')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('', include('shop.urls', namespace='shop')),
]

if settings.DEBUG is False:  # Используем is False для продакшена
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# --- СКРЫВАЕМ DJANGO Q ИЗ АДМИНКИ ---
# Этот код выполняется после загрузки всех приложений
try:
    from django.contrib import admin
    from django_q.models import Schedule, Task, Success, Failure, OrmQ

    # Список моделей, которые нужно убрать
    q_models = [Schedule, Task, Success, Failure, OrmQ]

    for model in q_models:
        # Проверяем, есть ли они в админке, и удаляем
        if admin.site.is_registered(model):
            admin.site.unregister(model)
except Exception:
    pass  # Если возникла ошибка (например, библиотека не установлена), просто игнорируем
    pass # Если их нет или уже скрыты — игнорируем