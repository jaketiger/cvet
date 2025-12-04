# orders/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from decimal import Decimal
from django_q.tasks import async_task
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET

from .models import Order, OrderItem
from .forms import OrderCreateForm, OneClickOrderForm
from cart.cart import Cart
from users.models import Profile
from shop.models import SiteSettings, Product, Postcard
from promo.models import PromoCode
from .utils import generate_time_slots, is_shop_open_now


@transaction.atomic
@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('shop:product_list_all')

    site_settings = SiteSettings.get_solo()
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST, request.FILES)
        if form.is_valid():
            # Проверка наличия товаров
            for item in cart:
                product = item['product']
                if product.stock < item['quantity']:
                    error_message = f"Извините, товара '{product.name}' на складе осталось только {product.stock} шт."
                    form.add_error(None, error_message)
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

            # Создание заказа (форма сама установит postcard и postcard_final_price)
            order = form.save(commit=False)
            order.user = request.user

            # Отладочная информация
            print(f"DEBUG views.py: order.postcard = {order.postcard}")
            print(f"DEBUG views.py: order.postcard_final_price = {order.postcard_final_price}")

            # Промокоды
            if hasattr(cart, 'promo') and cart.promo:
                order.promo_code = cart.promo
                order.discount = cart.promo.discount

            # Доставка и профиль
            if form.cleaned_data['delivery_option'] == 'delivery':
                order.delivery_cost = site_settings.delivery_cost
                profile.phone = form.cleaned_data['phone']
                profile.address = form.cleaned_data['address']
                profile.postal_code = form.cleaned_data['postal_code']
                profile.city = form.cleaned_data['city']
                profile.save()
            else:
                order.delivery_cost = Decimal('0.00')

            # Сохраняем заказ (postcard_final_price уже установлена в форме)
            order.save()

            # Если есть кастомное фото, сохраняем его
            if 'custom_postcard_image' in request.FILES:
                print("DEBUG views.py: Сохранение кастомного фото")
                order.custom_postcard_image = request.FILES['custom_postcard_image']
                order.save(update_fields=['custom_postcard_image'])

            # Создание позиций и обновление остатков
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

            # Очистка корзины
            cart.clear()

            if 'promo_id' in request.session:
                del request.session['promo_id']

            # Отправка email
            base_url = f"{request.scheme}://{request.get_host()}"
            async_task(
                'orders.utils.send_order_creation_emails_task',
                order_id=order.id,
                base_url=base_url
            )

            request.session['order_id'] = order.id
            return redirect('orders:order_created')
    else:
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
    """ИСПРАВЛЕННАЯ: Страница успешного оформления заказа"""
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('shop:product_list_all')

    try:
        order = Order.objects.get(id=order_id)

        # ИСПРАВЛЕНО: Добавляем атрибуты для корректного отображения
        order.delivery_time_display = order.get_delivery_time_display()

        # DEBUG: Проверяем сохраненные данные
        print(f"DEBUG created.html: order.id = {order.id}")
        print(f"DEBUG created.html: order.postcard_final_price = {order.postcard_final_price}")
        print(f"DEBUG created.html: order.postcard = {order.postcard}")
        print(f"DEBUG created.html: order.custom_postcard_image = {order.custom_postcard_image}")
        print(f"DEBUG created.html: order.get_total_cost() = {order.get_total_cost()}")

        # Удаляем ID из сессии
        if 'order_id' in request.session:
            del request.session['order_id']

        return render(request, 'orders/created.html', {'order': order})

    except Order.DoesNotExist:
        return redirect('shop:product_list_all')


@require_POST
def one_click_order(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = OneClickOrderForm(request.POST)

    if form.is_valid():
        if product.stock < 1:
            return JsonResponse({'success': False, 'error': 'Товара нет в наличии'})

        order = form.save(commit=False)
        order.is_one_click = True
        order.email = 'fast-order@no-email.com'
        order.last_name = '-'
        order.address = 'Заказ в 1 клик'
        order.city = '-'
        order.delivery_option = 'pickup'
        order.postcard_final_price = Decimal('0.00')
        order.postcard = None

        if request.user.is_authenticated:
            order.user = request.user

        order.save()

        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.price,
            quantity=1
        )

        product.stock -= 1
        product.save()

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
    date_str = request.GET.get('date')
    delivery_type = request.GET.get('type', 'delivery')

    if not date_str:
        return JsonResponse({'error': 'Date required'}, status=400)

    slots = generate_time_slots(date_str, mode=delivery_type)
    return JsonResponse({'slots': slots})


@require_GET
def check_asap(request):
    delivery_type = request.GET.get('type', 'delivery')
    is_open, reason = is_shop_open_now(mode=delivery_type)
    return JsonResponse({'is_open': is_open, 'reason': reason})