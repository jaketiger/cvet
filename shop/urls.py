# shop/urls.py

from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('cabinet/', views.cabinet, name='cabinet'),

    # --- НОВЫЙ МАРШРУТ ДЛЯ СТРАНИЦЫ КОНТАКТОВ ---
    path('contacts/', views.contact_page, name='contacts'),

    path('<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
]