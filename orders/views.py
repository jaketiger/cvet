# orders/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from decimal import Decimal
from django_q.tasks import async_task
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Order, OrderItem
from .forms import OrderCreateForm, OneClickOrderForm  # <--- Импорт новой формы
from cart.cart import Cart
from users.models import Profile
from shop.models import SiteSettings, Product, Postcard


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
            # Проверка наличия
            for item in cart:
                product = item['product']
                if product.stock < item['quantity']:
                    error_message = f"Извините, товара '{product.name}' на складе осталось только {product.stock} шт."
                    form.add_error(None, error_message)
                    postcards = Postcard.objects.filter(is_active=True)
                    return render(request, 'orders/create.html', {
                        'cart': cart,
                        'form': form,
                        'postcards': postcards,
                        'delivery_cost_js': site_settings.delivery_cost,
                        'cart_total_js': cart.get_total_price()
                    })

            order = form.save(commit=False)
            order.user = request.user

            if form.cleaned_data['delivery_option'] == 'delivery':
                order.delivery_cost = site_settings.delivery_cost
                # Обновляем профиль
                profile.phone = form.cleaned_data['phone']
                profile.address = form.cleaned_data['address']
                profile.postal_code = form.cleaned_data['postal_code']
                profile.city = form.cleaned_data['city']
                profile.save()
            else:
                order.delivery_cost = Decimal('0.00')

            order.save()

            # Обновление остатков
            products_to_update = []
            for item in cart:
                product = item['product']
                product.stock -= item['quantity']
                products_to_update.append(product)

                OrderItem.objects.create(order=order,
                                         product=product,
                                         price=item['price'],
                                         quantity=item['quantity'])

            Product.objects.bulk_update(products_to_update, ['stock'])
            cart.clear()

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

    postcards = Postcard.objects.filter(is_active=True)

    return render(request, 'orders/create.html', {
        'cart': cart,
        'form': form,
        'postcards': postcards,
        'delivery_cost_js': site_settings.delivery_cost,
        'cart_total_js': cart.get_total_price()
    })


def order_created(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('shop:product_list_all')
    try:
        order = Order.objects.get(id=order_id)
        if 'order_id' in request.session:
            del request.session['order_id']
        return render(request, 'orders/created.html', {'order': order})
    except Order.DoesNotExist:
        return redirect('shop:product_list_all')


# === VIEW ДЛЯ ЗАКАЗА В 1 КЛИК ===
@require_POST
def one_click_order(request, product_id):
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
        order.delivery_option = 'pickup'  # Менеджер уточнит

        if request.user.is_authenticated:
            order.user = request.user

        order.save()

        # Создаем товар в заказе
        OrderItem.objects.create(
            order=order,
            product=product,
            price=product.price,
            quantity=1
        )

        # Списываем остаток
        product.stock -= 1
        product.save()

        # Отправляем уведомление админу (можно асинхронно)
        base_url = f"{request.scheme}://{request.get_host()}"
        async_task(
            'orders.utils.send_order_creation_emails_task',
            order_id=order.id,
            base_url=base_url
        )

        return JsonResponse({'success': True, 'order_id': order.id})

    return JsonResponse({'success': False, 'error': 'Неверный формат телефона'})