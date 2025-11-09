# shop/views.py

from django.shortcuts import render, get_object_or_404
from .models import Category, Product
# Добавляем импорт для защиты страницы
from django.contrib.auth.decorators import login_required


# Ваша view для списка товаров (она у вас уже есть)
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request,
                  'shop/product_list.html',
                  {'category': category,
                   'categories': categories,
                   'products': products})


# Ваша view для детальной страницы (она у вас уже есть)
def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    # ... (здесь может быть логика для формы добавления в корзину) ...
    return render(request,
                  'shop/product_detail.html',
                  {'product': product})


# УБЕДИТЕСЬ, ЧТО ЭТОТ КОД ДОБАВЛЕН В КОНЕЦ ФАЙЛА
@login_required
def cabinet(request):
    # Получаем все заказы текущего пользователя
    orders = request.user.orders.all().order_by('-created')

    # Передаем заказы в шаблон для отображения
    return render(request, 'shop/cabinet.html', {'orders': orders})
