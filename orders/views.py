# orders/views.py

from django.shortcuts import render, redirect  # <-- Добавлен redirect
from .models import Order, OrderItem  # <-- Добавлен Order
from .forms import OrderCreateForm
from cart.cart import Cart
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from shop.models import Profile


@login_required
def order_create(request):
    cart = Cart(request)

    # --- НОВАЯ ЗАЩИТА ОТ ПУСТЫХ ЗАКАЗОВ ---
    # Если в корзине нет товаров, просто перенаправляем пользователя в каталог.
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

            subject = f'Заказ #{order.id} - MegaCvet'
            message = (f'Здравствуйте, {order.first_name}!\n\n'
                       f'Вы успешно оформили заказ #{order.id}.\n'
                       f'Сумма к оплате: {order.get_total_cost()} руб.\n\n'
                       f'Спасибо за покупку!')
            send_mail(
                subject, message, settings.EMAIL_HOST_USER,
                [order.email], fail_silently=False,
            )

            # --- ГЛАВНОЕ ИЗМЕНЕНИЕ (Post/Redirect/Get) ---
            # Сохраняем ID заказа в сессии, чтобы передать его на следующую страницу.
            request.session['order_id'] = order.id
            # Перенаправляем пользователя на новую страницу "Спасибо".
            return redirect('orders:order_created')
    else:
        # Предзаполнение формы (остается без изменений)
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


# --- НОВАЯ VIEW ДЛЯ СТРАНИЦЫ "СПАСИБО ЗА ЗАКАЗ" ---
def order_created(request):
    """
    Эта view безопасно отображает страницу подтверждения,
    получая ID заказа из сессии.
    """
    order_id = request.session.get('order_id')

    # Если кто-то зашел на эту страницу напрямую, без заказа, отправляем его в каталог
    if not order_id:
        return redirect('shop:product_list')

    try:
        order = Order.objects.get(id=order_id)
        # Очищаем сессию от ID заказа после того, как мы его получили.
        # Это предотвратит повторный показ этой страницы.
        del request.session['order_id']
        return render(request, 'orders/created.html', {'order': order})
    except Order.DoesNotExist:
        # Если заказа с таким ID нет, тоже отправляем в каталог
        return redirect('shop:product_list')