# orders/urls.py

from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Старый маршрут для страницы с формой заказа
    path('create/', views.order_create, name='order_create'),

    # НОВЫЙ маршрут для страницы "Спасибо", на которую будет перенаправлять
    path('created/', views.order_created, name='order_created'),
]