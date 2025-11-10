# orders/views.py

from django.shortcuts import render, redirect
from .models import Order, OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.contrib.auth.decorators import login_required
from shop.models import Profile, SiteSettings
from django.conf import settings
from django.core.mail import send_mail
from decimal import Decimal


@login_required
def order_create(request):
    cart = Cart(request)
    if len(cart) == 0:
        return redirect('shop:product_list')

    site_settings = SiteSettings.get_solo()
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user

            if form.cleaned_data['delivery_option'] == 'delivery':
                order.delivery_cost = site_settings.delivery_cost
                # Обновляем профиль только если была доставка
                profile.phone = form.cleaned_data['phone']
                profile.address = form.cleaned_data['address']
                profile.postal_code = form.cleaned_data['postal_code']
                profile.city = form.cleaned_data['city']
                profile.save()
            else:
                order.delivery_cost = Decimal('0.00')

            order.save()

            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'],
                                         price=item['price'], quantity=item['quantity'])
            cart.clear()

            # --- Блок отправки email ---
            subject = f'Подтверждение заказа #{order.id} - MegaCvet'
            message_body = []
            message_body.append(f'Здравствуйте, {order.first_name}!')
            message_body.append(f'Вы успешно оформили заказ #{order.id}.\n')
            message_body.append('Состав вашего заказа:')
            for item in order.items.all():
                message_body.append(f'- {item.product.name} ({item.quantity} шт.) - {item.get_cost()} руб.')

            message_body.append(f'\nСтоимость товаров: {order.get_items_cost()} руб.')
            message_body.append(f'Стоимость доставки: {order.delivery_cost} руб.')
            message_body.append(f'Итого к оплате: {order.get_total_cost()} руб.\n')

            if order.delivery_option == 'delivery':
                message_body.append('Адрес доставки:')
                message_body.append(f'{order.postal_code}, {order.city}, {order.address}')
            else:
                message_body.append('Способ получения: Самовывоз.')
            message_body.append(f'Телефон для связи: {order.phone}\n')
            message_body.append('Спасибо за покупку!')
            message = '\n'.join(message_body)
            send_mail(subject, message, settings.EMAIL_HOST_USER, [order.email], fail_silently=False)
            # ---------------------------

            request.session['order_id'] = order.id
            return redirect('orders:order_created')
    else:
        # --- БЛОК ELSE С ПРАВИЛЬНЫМИ ОТСТУПАМИ ---
        # Этот код выполняется, когда пользователь просто открывает страницу
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
        return redirect('shop:product_list')

    try:
        order = Order.objects.get(id=order_id)
        if 'order_id' in request.session:
            del request.session['order_id']
        return render(request, 'orders/created.html', {'order': order})
    except Order.DoesNotExist:
        return redirect('shop:product_list')