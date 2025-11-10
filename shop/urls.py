# shop/urls.py

from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = 'shop'

urlpatterns = [
    # Главная страница (с баннером)
    path('', views.home_page, name='home'),

    # Страница со всеми товарами
    path('catalog/', views.product_list_all, name='product_list_all'),

    # Страница конкретной категории
    path('category/<slug:category_slug>/', views.product_list_by_category, name='product_list_by_category'),

    # Детальная страница товара
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product_detail'),

    # Кабинет и контакты
    path('cabinet/', views.cabinet, name='cabinet'),
    path('contacts/', views.contact_page, name='contacts'),

#    path('about/', TemplateView.as_view(template_name="shop/about.html"), name='about'),
#    path('payment/', TemplateView.as_view(template_name="shop/payment.html"), name='payment'),
#    path('terms/', TemplateView.as_view(template_name="shop/terms.html"), name='terms'),
# --- ОБНОВЛЕННЫЕ МАРШРУТЫ ДЛЯ СТАТИЧЕСКИХ СТРАНИЦ ---
    path('about/', views.about_page, name='about'),
    path('payment/', views.payment_page, name='payment'),
    path('terms/', views.terms_page, name='terms'),

]