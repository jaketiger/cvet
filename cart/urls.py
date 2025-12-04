# cart/urls.py

from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    # ДОБАВЛЕНО: Для работы с открытками в корзине
    path('add-postcard/<int:product_id>/', views.add_postcard_to_cart, name='add_postcard'),
    path('remove-postcard/<int:product_id>/', views.remove_postcard_from_cart, name='remove_postcard'),
]