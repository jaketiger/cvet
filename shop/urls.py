# shop/urls.py
from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = 'shop'

urlpatterns = [
    # Маршруты для каталога
    path('', views.home_page, name='home'),
    path('catalog/', views.product_list_all, name='product_list_all'),
    path('category/<slug:category_slug>/', views.product_list_by_category, name='product_list_by_category'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),

    # --- Маршрут для поиска ---
    path('search/', views.search_results, name='search_results'), # <-- ДОБАВЛЕНО

    # --- Маршруты для личного кабинета ---
    path('cabinet/', views.cabinet, name='cabinet'),
    path('cabinet/profile/', views.profile_edit, name='profile_edit'),
    path('cabinet/order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cabinet/order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),


    # --- Статические страницы ---
    path('contacts/', views.contact_page, name='contacts'),
    path('page/<slug:slug>/', views.footer_page_detail, name='footer_page_detail'),

    # --- AJAX URL ---
    path('get-product-price/', views.get_product_price, name='get_product_price'),
]