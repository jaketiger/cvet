# megacvet_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Импортируем стандартные view для входа/выхода и нашу новую форму
from django.contrib.auth import views as auth_views
from users.forms import LoginForm  # <-- Убедитесь, что 'users' - правильное имя вашего приложения

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- НОВЫЕ МАРШРУТЫ ДЛЯ АУТЕНТИФИКАЦИИ ---
    # Маршрут для страницы входа
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(
            template_name='registration/login.html',
            authentication_form=LoginForm  # <-- Используем нашу кастомную форму
        ),
        name='login'
    ),

    # Маршрут для выхода из системы
    path(
        'accounts/logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),

    # Подключаем URL'ы из нашего приложения users (для регистрации)
    # Эта строка должна идти ПОСЛЕ явного определения login и logout
    path('accounts/', include('users.urls')),

    # URL'ы остальных приложений
    path('cart/', include('cart.urls', namespace='cart')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('', include('shop.urls', namespace='shop')),
]

# Этот блок кода нужен для отображения картинок (media) в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)