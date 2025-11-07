# shop/urls.py

from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Этот маршрут у вас уже есть
    path('', views.product_list, name='product_list'),

    # --- ДОБАВЬТЕ ЭТОТ НОВЫЙ МАРШРУТ ---
    # <slug:slug> - это "переменная" в URL. Django передаст ее
    # значение в нашу view-функцию product_detail.
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
]