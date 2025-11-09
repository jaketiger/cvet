# shop/urls.py

from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # Этот путь отвечает за главную страницу
    path('', views.product_list, name='product_list'),

    # УБЕДИТЕСЬ, ЧТО ЭТА СТРОЧКА ЕСТЬ И РАСКОММЕНТИРОВАНА
    path('cabinet/', views.cabinet, name='cabinet'),

    # Этот путь для категорий
    path('<slug:category_slug>/', views.product_list, name='product_list_by_category'),

    # Этот путь для детальной страницы товара
    path('<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),
]