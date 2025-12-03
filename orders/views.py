# orders/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from decimal import Decimal
from django_q.tasks import async_task
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Order, OrderItem
from .forms import OrderCreateForm, OneClickOrderForm
from cart.cart import Cart
from users.models import Profile
from shop.models import SiteSettings, Product, Postcard
from promo.models import PromoCode
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .utils import generate_time_slots, is_shop_open_now


@transaction.atomic
@login_required
def order_create(request):
    """
    Оформление обычного заказа из корзины.
    """
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('shop:product_list_all')

    site_settings = SiteSettings.get_solo()
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST, request.FILES)
        if form.is_valid():
            # 1. Проверка наличия товаров на складе перед сохранением
            for item in cart:
                product = item['product']
                if product.stock < item['quantity']:
                    error_message = f"Извините, товара '{product.name}' на складе осталось только {product.stock} шт."
                    form.add_error(None, error_message)

                    # При ошибке перезагружаем открытки
                    postcards = Postcard.objects.filter(is_active=True).order_by('price', 'order')
                    cart_total = cart.get_total_price_after_discount() if hasattr(cart,
                                                                                  'get_total_price_after_discount') else cart.get_total_price()

                    return render(request, 'orders/create.html', {
                        'cart': cart,
                        'form': form,
                        'postcards': postcards,
                        'delivery_cost_js': site_settings.delivery_cost,
                        'cart_total_js': cart_total
                    })

            # 2. Создание объекта заказа
            # Теперь форма сама обработает postcard через переопределенный save()
            order = form.save(commit=False)
            order.user = request.user

            # Промокоды
            if hasattr(cart, 'promo') and cart.promo:
                order.promo_code = cart.promo
                order.discount = cart.promo.discount

            # 3. Логика доставки и обновления профиля
            if form.cleaned_data['delivery_option'] == 'delivery':
                order.delivery_cost = site_settings.delivery_cost
                profile.phone = form.cleaned_data['phone']
                profile.address = form.cleaned_data['address']
                profile.postal_code = form.cleaned_data['postal_code']
                profile.city = form.cleaned_data['city']
                profile.save()
            else:
                order.delivery_cost = Decimal('0.00')

            # 4. Сохраняем заказ в БД
            order.save()

            # 5. Создаем позиции заказа и обновляем остатки
            products_to_update = []
            for item in cart:
                product = item['product']
                product.stock -= item['quantity']
                products_to_update.append(product)

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=item['price'],
                    quantity=item['quantity']
                )

            Product.objects.bulk_update(products_to_update, ['stock'])

            # 6. Очищаем корзину
            cart.clear()

            if 'promo_id' in request.session:
                del request.session['promo_id']

            # 7. Запускаем асинхронную задачу
            base_url = f"{request.scheme}://{request.get_host()}"
            async_task(
                'orders.utils.send_order_creation_emails_task',
                order_id=order.id,
                base_url=base_url
            )

            # 8. Сохраняем ID заказа в сессию
            request.session['order_id'] = order.id
            return redirect('orders:order_created')
    else:
        # GET-запрос: предзаполняем форму данными из профиля
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': profile.phone,
            'address': profile.address,
            'postal_code': profile.postal_code,
            'city': profile.city,
        }
        form = OrderCreateForm(initial=initial_data)

    postcards = Postcard.objects.filter(is_active=True).order_by('price', 'order')

    if hasattr(cart, 'get_total_price_after_discount'):
        cart_total_js = cart.get_total_price_after_discount()
    else:
        cart_total_js = cart.get_total_price()

    return render(request, 'orders/create.html', {
        'cart': cart,
        'form': form,
        'postcards': postcards,
        'delivery_cost_js': site_settings.delivery_cost,
        'cart_total_js': cart_total_js
    })


def order_created(request):
    """
    Страница успешного оформления заказа.
    """
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('shop:product_list_all')

    try:
        order = Order.objects.get(id=order_id)
        # Удаляем ID из сессии
        if 'order_id' in request.session:
            del request.session['order_id']
        return render(request, 'orders/created.html', {'order': order})
    except Order.DoesNotExist:
        return redirect('shop:product_list_all')


@require_POST
def one_click_order(request, product_id):
    """
    Обработчик быстрого заказа в 1 клик (AJAX).
    Промокоды здесь НЕ применяются (для упрощения).
    """
    product = get_object_or_404(Product, id=product_id)
    form = OneClickOrderForm(request.POST)

    if form.is_valid():
        # Проверка наличия
        if product.stock < 1:
            return JsonResponse({'success': False, 'error': 'Товара нет в наличии'})

        order = form.save(commit=False)

        # Заполняем технические поля заглушками
        order.is_one_click = True
        order.email = 'fast-order@no-email.com'
        order.last_name = '-'
        order.address = 'Заказ в 1 клик'
        order.city = '-'
        order.delivery_option = 'pickup'  # Менеджер уточнит детали

        if request.user.is_authenticated:
            order.user = request.user

        order.save()

        # Создаем товар в заказе (всегда 1 шт)
        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.price,
            quantity=1
        )

        # Списываем остаток
        product.stock -= 1
        product.save()

        # Отправляем уведомление
        base_url = f"{request.scheme}://{request.get_host()}"
        async_task(
            'orders.utils.send_order_creation_emails_task',
            order_id=order.id,
            base_url=base_url
        )

        return JsonResponse({'success': True, 'order_id': order.id})

    return JsonResponse({'success': False, 'error': 'Неверный формат телефона или имени'})


@require_GET
def get_time_slots(request):
    """
    API для получения доступных интервалов.
    URL: /orders/api/get-slots/?date=2023-10-25&type=delivery
    """
    date_str = request.GET.get('date')
    delivery_type = request.GET.get('type', 'delivery')  # 'delivery' или 'pickup'

    if not date_str:
        return JsonResponse({'error': 'Date required'}, status=400)

    slots = generate_time_slots(date_str, mode=delivery_type)

    return JsonResponse({'slots': slots})


@require_GET
def check_asap(request):
    """
    API для проверки доступности 'Как можно быстрее'.
    URL: /orders/api/check-asap/?type=delivery
    """
    delivery_type = request.GET.get('type', 'delivery')
    is_open, reason = is_shop_open_now(mode=delivery_type)

    return JsonResponse({'is_open': is_open, 'reason': reason})