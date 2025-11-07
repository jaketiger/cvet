from django.shortcuts import render

# Create your views here.

# shop/views.py

# Добавляем get_object_or_404
from django.shortcuts import render, get_object_or_404
from .models import Category, Product

# Эта функция у вас уже есть
def product_list(request):
    products = Product.objects.filter(available=True)
    return render(request,
                  'shop/product_list.html',
                  {'products': products})

# --- ДОБАВЬТЕ ЭТУ НОВУЮ ФУНКЦИЮ ---
def product_detail(request, slug):
    # Мы ищем товар по slug. Если он не найден, Django вернет страницу 404
    product = get_object_or_404(Product,
                                slug=slug,
                                available=True)
    return render(request,
                  'shop/product_detail.html',
                  {'product': product})
