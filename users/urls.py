# users/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import LoginForm

app_name = 'users'  # <--- Это важно для LOGIN_URL = 'users:login'

urlpatterns = [
    path('register/', views.register, name='register'),

    # Вход
    path('login/', auth_views.LoginView.as_view(
        template_name='users/login.html',  # Указываем наш новый шаблон
        authentication_form=LoginForm
    ), name='login'),

    # Выход
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]