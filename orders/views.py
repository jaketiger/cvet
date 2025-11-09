# orders/views.py

from django.shortcuts import render
from .models import OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.contrib.auth.decorators import login_required  # <-- Важный импорт


@login_required  # <-- Этот декоратор теперь защищает всю страницу
def order_create(request):
    cart = Cart(request)
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()

            # --- НОВЫЙ БЛОК: ОБНОВЛЯЕМ ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ---
            profile = request.user.profile
            profile.phone = form.cleaned_data['phone']
            profile.address = form.cleaned_data['address']
            profile.postal_code = form.cleaned_data['postal_code']
            profile.city = form.cleaned_data['city']
            profile.save()
            # -----------------------------------------------

            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'],
                                         price=item['price'], quantity=item['quantity'])
            cart.clear()
            return render(request, 'orders/created.html', {'order': order})
    else:
        # --- НОВЫЙ БЛОК: ПРЕДЗАПОЛНЯЕМ ФОРМУ ИЗ ПРОФИЛЯ ---
        try:
            profile = request.user.profile
            initial_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email,
                # Берем данные из профиля
                'phone': profile.phone,
                'address': profile.address,
                'postal_code': profile.postal_code,
                'city': profile.city,
            }
            form = OrderCreateForm(initial=initial_data)
        except:  # На случай, если у старых пользователей еще нет профиля
            form = OrderCreateForm()
        # ----------------------------------------------------

    return render(request, 'orders/create.html', {'cart': cart, 'form': form})