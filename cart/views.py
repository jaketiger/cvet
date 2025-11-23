# cart/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from shop.models import Product
from .cart import Cart
from .forms import CartAddProductForm
from django.http import JsonResponse


@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)

    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product,
                 quantity=cd['quantity'],
                 update_quantity=cd['update'],
                 postcard_text=cd.get('postcard_text'))

    # ИСПРАВЛЕНИЕ: Строгая проверка на AJAX.
    # Теперь JSON возвращается ТОЛЬКО если JS явно об этом попросил через заголовок.
    # Во всех остальных случаях (включая кнопки в корзине) будет редирект.
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if is_ajax:
        return JsonResponse({
            'success': True,
            'cart_len': len(cart),
            'total_price': cart.get_total_price()
        })

    # Если это не AJAX (например, кнопки +/- в корзине), просто перезагружаем страницу
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)

    # Флаг, который будет разрешать или запрещать оформление заказа
    is_checkout_possible = True

    for item in cart:
        # По-прежнему создаем форму для обновления количества
        item['update_quantity_form'] = CartAddProductForm(
            initial={'quantity': item['quantity'], 'update': True}
        )

        # Проверяем, достаточно ли товара на складе
        product = item['product']
        if product.stock < item['quantity']:
            # Если товара не хватает, помечаем этот элемент и блокируем оформление
            item['is_stock_sufficient'] = False
            is_checkout_possible = False
        else:
            # Если все в порядке, тоже ставим флаг
            item['is_stock_sufficient'] = True

    # Передаем в шаблон оба флага: и для всей корзины, и для каждого товара
    return render(request, 'cart/detail.html', {
        'cart': cart,
        'is_checkout_possible': is_checkout_possible
    })