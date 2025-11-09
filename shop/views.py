# shop/views.py

from django.shortcuts import render, get_object_or_404
from .models import Category, Product
from django.contrib.auth.decorators import login_required
from cart.forms import CartAddProductForm  # <-- ДОБАВЛЕН НЕОБХОДИМЫЙ ИМПОРТ


# View для списка товаров (остается без изменений)
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


# View для детальной страницы (ИЗМЕНЕНА)
def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)

    # Создаем экземпляр формы для добавления в корзину, чтобы передать его в шаблон
    cart_product_form = CartAddProductForm()

    return render(request,
                  'shop/product_detail.html',
                  {'product': product,
                   'cart_product_form': cart_product_form})  # <-- Передаем форму в контекст


# View для личного кабинета (остается без изменений)
@login_required
def cabinet(request):
    # Получаем все заказы текущего пользователя
    orders = request.user.orders.all().order_by('-created')

    # Передаем заказы в шаблон для отображения
    return render(request, 'shop/cabinet.html', {'orders': orders})