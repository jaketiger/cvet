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

    # --- Явные URL'ы для сброса пароля ---
    # 1. Форма запроса сброса (использует нашу кастомную view)
    path('accounts/password_reset/', user_views.password_reset_request, name='password_reset'),

    # 2. Сообщение "Проверьте почту" (использует стандартную view)
    path('accounts/password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),

    # 3. Ссылка из письма, ведущая на форму ввода нового пароля
    path('accounts/reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),

    # 4. Сообщение об успешном сбросе
    path('accounts/reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

    # 3. URL-адреса наших приложений
    path('accounts/', include('users.urls')),  # Для регистрации
    path('cart/', include('cart.urls', namespace='cart')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('', include('shop.urls', namespace='shop')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)