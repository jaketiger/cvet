# orders/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from decimal import Decimal
from django_q.tasks import async_task

from .models import Order, OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from shop.models import Profile, SiteSettings, Product


@transaction.atomic
@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('shop:product_list_all')

    site_settings = SiteSettings.get_solo()
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():

            # Сначала проверяем наличие всех товаров на складе перед созданием заказа
            for item in cart:
                product = item['product']
                if product.stock < item['quantity']:
                    # Если какого-то товара не хватает, прерываем заказ и выводим ошибку
                    error_message = f"Извините, товара '{product.name}' на складе осталось только {product.stock} шт. Пожалуйста, измените количество в корзине."
                    form.add_error(None, error_message)
                    return render(request, 'orders/create.html', {
                        'cart': cart,
                        'form': form,
                        'delivery_cost_js': site_settings.delivery_cost,
                        'cart_total_js': cart.get_total_price()
                    })

            # Если проверка прошла успешно, создаем заказ
            order = form.save(commit=False)
            order.user = request.user

            if form.cleaned_data['delivery_option'] == 'delivery':
                order.delivery_cost = site_settings.delivery_cost
                profile.phone = form.cleaned_data['phone']
                profile.address = form.cleaned_data['address']
                profile.postal_code = form.cleaned_data['postal_code']
                profile.city = form.cleaned_data['city']
                profile.save()
            else:
                order.delivery_cost = Decimal('0.00')

            order.save()

            # Создаем список товаров для массового обновления остатков
            products_to_update = []
            for item in cart:
                product = item['product']
                # Уменьшаем количество товара
                product.stock -= item['quantity']
                products_to_update.append(product)

                OrderItem.objects.create(order=order,
                                         product=product,
                                         price=item['price'],
                                         quantity=item['quantity'])

            # Массово обновляем остатки всех товаров одним запросом к БД
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

    return render(request, 'orders/create.html', {
        'cart': cart,
        'form': form,
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