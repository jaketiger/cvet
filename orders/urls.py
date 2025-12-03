# orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('created/', views.order_created, name='order_created'),

    path('api/get-slots/', views.get_time_slots, name='api_get_slots'),
    path('api/check-asap/', views.check_asap, name='api_check_asap'),

    # === НОВЫЙ URL ДЛЯ 1 КЛИКА ===
    path('one_click_order/<int:product_id>/', views.one_click_order, name='one_click_order'),
]