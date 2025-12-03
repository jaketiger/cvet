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

    # 2. Аутентификация (Вход / Выход)
    path('login/', auth_views.LoginView.as_view(
        template_name='users/login.html',
        authentication_form=LoginForm
    ), name='login'),

    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # 3. Сброс пароля (ОБНОВЛЕННЫЕ ПУТИ К ШАБЛОНАМ)

    # Этап 1: Ввод email (используем ваше кастомное view из users/views.py)
    path('password_reset/', user_views.password_reset_request, name='password_reset'),

    # Этап 2: Сообщение "Письмо отправлено"
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html'  # <--- Было registration/, стало users/
    ), name='password_reset_done'),

    # Этап 3: Ввод нового пароля (по ссылке из письма)
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html'  # <--- Было registration/, стало users/
    ), name='password_reset_confirm'),

    # Этап 4: Успешное завершение
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html'  # <--- Было registration/, стало users/
    ), name='password_reset_complete'),

    # 4. Подключение приложений
    path('users/', include('users.urls', namespace='users')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('', include('shop.urls', namespace='shop')),
    path('promo/', include('promo.urls', namespace='promo')),
    path('favorites/', include('favorites.urls', namespace='favorites')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Скрытие Django Q из админки
try:
    from django_q.models import Schedule, Task, Success, Failure, OrmQ

    q_models = [Schedule, Task, Success, Failure, OrmQ]
    for model in q_models:
        if admin.site.is_registered(model):
            admin.site.unregister(model)
except Exception:
    pass