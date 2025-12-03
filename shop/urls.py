# shop/urls.py

from django.urls import path
from . import views

app_name = 'shop'

urlpatterns = [
    # === ГЛАВНАЯ И КАТАЛОГ ===
    # ВАЖНО: name='home' (так написано в вашем base.html)
    path('', views.home_page, name='home'),

    path('catalog/', views.product_list_all, name='product_list_all'),
    path('category/<slug:category_slug>/', views.product_list_by_category, name='product_list_by_category'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),

    # === ПОИСК И AJAX ===
    path('search/', views.search_results, name='search_results'),
    path('get-product-price/', views.get_product_price, name='get_product_price'),

    # === ЛИЧНЫЙ КАБИНЕТ ===
    path('cabinet/', views.cabinet, name='cabinet'),
    path('cabinet/profile/', views.profile_edit, name='profile_edit'),
    path('cabinet/order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cabinet/order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),

    # === СТАТИЧЕСКИЕ СТРАНИЦЫ (Умный роутинг) ===
    # Ссылки для base.html
    path('contacts/', views.footer_page_detail, {'slug': 'contacts'}, name='contacts'),
    path('about/', views.footer_page_detail, {'slug': 'about'}, name='about'),
    path('payment/', views.footer_page_detail, {'slug': 'payment'}, name='payment'),
    path('terms/', views.footer_page_detail, {'slug': 'terms'}, name='terms'),

    # Универсальный путь для остальных страниц (должен быть в конце)
    path('page/<slug:slug>/', views.footer_page_detail, name='footer_page_detail'),
]