# orders/views.py

from django.shortcuts import render
from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from shop.models import Profile  # <-- Убедитесь, что Profile импортирован из shop.models


@login_required
def order_create(request):
    cart = Cart(request)

    # --- САМЫЙ НАДЕЖНЫЙ СПОСОБ РАБОТЫ С ПРОФИЛЕМ ---
    # Получаем профиль пользователя или создаем его, если он по какой-то причине отсутствует.
    # Это работает и для старых, и для новых пользователей и никогда не вызовет ошибку.
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            # Обновляем данные профиля из валидной формы
            profile.phone = form.cleaned_data['phone']
            profile.address = form.cleaned_data['address']
            profile.postal_code = form.cleaned_data['postal_code']
            profile.city = form.cleaned_data['city']
            profile.save()

            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'],
                                         price=item['price'], quantity=item['quantity'])
            cart.clear()

            # Отправка Email
            subject = f'Заказ #{order.id} - MegaCvet'
            message = (f'Здравствуйте, {order.first_name}!\n\n'
                       f'Вы успешно оформили заказ #{order.id}.\n'
                       f'Сумма к оплате: {order.get_total_cost()} руб.\n\n'
                       f'Спасибо за покупку!')
            send_mail(
                subject, message, settings.EMAIL_HOST_USER,
                [order.email], fail_silently=False,
            )

            return render(request, 'orders/created.html', {'order': order})
    else:
        # Предзаполняем форму данными из User и Profile
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