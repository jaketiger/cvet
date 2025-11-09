# orders/views.py

from django.shortcuts import render, redirect
from .models import Order, OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from shop.models import Profile


@login_required
def order_create(request):
    cart = Cart(request)

    if len(cart) == 0:
        return redirect('shop:product_list')

    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            profile.phone = form.cleaned_data['phone']
            profile.address = form.cleaned_data['address']
            profile.postal_code = form.cleaned_data['postal_code']
            profile.city = form.cleaned_data['city']
            profile.save()

            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'],
                                         price=item['price'], quantity=item['quantity'])

            cart.clear()

            # --- ОБНОВЛЕННЫЙ БЛОК ОТПРАВКИ EMAIL ---
            subject = f'Подтверждение заказа #{order.id} - MegaCvet'

            message_body = []
            message_body.append(f'Здравствуйте, {order.first_name}!')
            message_body.append(f'Вы успешно оформили заказ #{order.id} в нашем магазине.\n')

            # Добавляем состав заказа
            message_body.append('Состав вашего заказа:')
            for item in order.items.all():
                message_body.append(
                    f'- {item.product.name} ({item.quantity} шт.) - {item.get_cost()} руб.'
                )

            message_body.append(f'\nИтого к оплате: {order.get_total_cost()} руб.\n')

            # --- НОВАЯ ЧАСТЬ: АДРЕС ДОСТАВКИ ---
            message_body.append('Адрес доставки:')
            message_body.append(f'{order.postal_code}, {order.city}')
            message_body.append(f'{order.address}')
            message_body.append(f'Телефон для связи: {order.phone}\n')
            # ------------------------------------

            message_body.append('Спасибо за покупку!')

            message = '\n'.join(message_body)

            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [order.email],
                fail_silently=False,
            )
            # ------------------------------------

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

    return render(request, 'orders/create.html', {'cart': cart, 'form': form})


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