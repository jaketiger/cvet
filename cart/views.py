from django.shortcuts import render

# Create your views here.

# cart/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart
# from .forms import CartAddProductForm # Это мы добавим позже

@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    # Пока не используем форму, просто добавляем 1 товар
    quantity = 1
    cart.add(product=product, quantity=quantity, update_quantity=False)
    # После добавления перенаправляем на страницу корзины
    return redirect('cart:cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')

def cart_detail(request):
    cart = Cart(request)
    return render(request, 'cart/detail.html', {'cart': cart})
