# cart/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from shop.models import Product, Postcard
from .cart import Cart
from .forms import CartAddProductForm
from django.http import JsonResponse
from decimal import Decimal


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

        # Обработка открытки если передана (ДОБАВЛЕНО)
        postcard_id = request.POST.get('postcard_id')
        if postcard_id and postcard_id != 'none' and postcard_id != '':
            try:
                postcard = Postcard.objects.get(id=int(postcard_id))
                cart.add_postcard_to_product(
                    product_id=product_id,
                    postcard_id=postcard.id,
                    postcard_price=postcard.price,
                    postcard_title=postcard.title
                )
            except (Postcard.DoesNotExist, ValueError):
                pass

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    if is_ajax:
        return JsonResponse({
            'success': True,
            'cart_len': len(cart),
            'total_price': str(cart.get_total_price())
        })

    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    is_checkout_possible = True

    # Рассчитываем общую стоимость открыток
    postcards_total = Decimal('0.00')

    for item in cart:
        # Создаем форму для обновления количества
        item['update_quantity_form'] = CartAddProductForm(
            initial={'quantity': item['quantity'], 'update': True}
        )

        # Проверяем наличие товара на складе
        product = item['product']
        if product.stock < item['quantity']:
            item['is_stock_sufficient'] = False
            is_checkout_possible = False
        else:
            item['is_stock_sufficient'] = True

        # Рассчитываем стоимость открытки для этого товара (ДОБАВЛЕНО)
        if item.get('postcard_info') and 'price' in item['postcard_info']:
            try:
                postcard_price = Decimal(str(item['postcard_info']['price']))
                item['postcard_price'] = postcard_price
                postcards_total += postcard_price
            except (ValueError, TypeError):
                item['postcard_price'] = Decimal('0.00')
        else:
            item['postcard_price'] = Decimal('0.00')

    # Получаем информацию о промокоде и скидке (ДОБАВЛЕНО)
    promo_discount = Decimal('0.00')
    promo_code = None
    if cart.promo:
        promo_discount = cart.get_discount()
        promo_code = cart.promo.code

    # Рассчитываем итоговую сумму с учетом открыток и промокода (ДОБАВЛЕНО)
    total_items = cart.get_total_price()

    if cart.promo:
        total_after_discount = cart.get_total_price_after_discount() + postcards_total
    else:
        total_after_discount = total_items + postcards_total

    return render(request, 'cart/detail.html', {
        'cart': cart,
        'is_checkout_possible': is_checkout_possible,
        'postcards_total': postcards_total,  # ДОБАВЛЕНО
        'promo_discount': promo_discount,  # ДОБАВЛЕНО
        'promo_code': promo_code,  # ДОБАВЛЕНО
        'total_items': total_items,  # ДОБАВЛЕНО
        'total_after_discount': total_after_discount,  # ДОБАВЛЕНО
    })


# ДОБАВЛЕНО: Функции для работы с открытками в корзине
@require_POST
def add_postcard_to_cart(request, product_id):
    """Добавляет открытку к товару в корзине (AJAX)"""
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    postcard_id = request.POST.get('postcard_id')

    # Проверяем, есть ли товар в корзине
    product_id_str = str(product_id)
    if product_id_str not in cart.cart:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'error': 'Товар не найден в корзине'
            })
        return redirect('cart:cart_detail')

    if postcard_id and postcard_id != 'none' and postcard_id != '':
        try:
            postcard = Postcard.objects.get(id=int(postcard_id))
            success = cart.add_postcard_to_product(
                product_id=product_id,
                postcard_id=postcard.id,
                postcard_price=postcard.price,
                postcard_title=postcard.title
            )

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                if success:
                    # Пересчитываем итоги
                    postcards_total = cart.get_postcard_total()
                    if cart.promo:
                        total_after = cart.get_total_price_after_discount() + postcards_total
                    else:
                        total_after = cart.get_total_price() + postcards_total

                    return JsonResponse({
                        'success': True,
                        'postcard_total': str(postcards_total),
                        'total_after_discount': str(total_after),
                        'postcard_title': postcard.title,
                        'postcard_price': str(postcard.price)
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'error': 'Не удалось добавить открытку'
                    })
        except (Postcard.DoesNotExist, ValueError):
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Открытка не найдена'
                })

    return redirect('cart:cart_detail')


@require_POST
def remove_postcard_from_cart(request, product_id):
    """Удаляет открытку у товара в корзине (AJAX)"""
    cart = Cart(request)
    success = cart.remove_postcard_from_product(product_id)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if success:
            # Пересчитываем итоги
            postcards_total = cart.get_postcard_total()
            if cart.promo:
                total_after = cart.get_total_price_after_discount() + postcards_total
            else:
                total_after = cart.get_total_price() + postcards_total

            return JsonResponse({
                'success': True,
                'postcard_total': str(postcards_total),
                'total_after_discount': str(total_after)
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Не удалось удалить открытку'
            })

    return redirect('cart:cart_detail')


# ДОБАВЛЕНО: Функция для обновления текста открытки
@require_POST
def update_postcard_text(request, product_id):
    """Обновляет текст открытки для товара в корзине (AJAX)"""
    cart = Cart(request)
    product_id_str = str(product_id)

    if product_id_str not in cart.cart:
        return JsonResponse({
            'success': False,
            'error': 'Товар не найден в корзине'
        })

    postcard_text = request.POST.get('postcard_text', '').strip()

    # Сохраняем текст открытки в сессии
    if 'postcard_texts' not in request.session:
        request.session['postcard_texts'] = {}

    request.session['postcard_texts'][product_id_str] = postcard_text
    request.session.modified = True

    return JsonResponse({
        'success': True,
        'postcard_text': postcard_text
    })