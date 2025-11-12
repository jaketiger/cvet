# orders/views.py

from django.shortcuts import render, redirect
from django.urls import reverse
from .models import Order, OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.contrib.auth.decorators import login_required
from shop.models import Profile, SiteSettings
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from decimal import Decimal
from django.template.loader import render_to_string

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

            for item in cart:
                OrderItem.objects.create(order=order, product=item['product'],
                                         price=item['price'], quantity=item['quantity'])
            cart.clear()

            # --- ВОЗВРАЩАЕМ ПРЯМУЮ ОТПРАВКУ EMAIL ---
            # 1. Отправляем письмо клиенту
            send_order_confirmation_email(order)

            # 2. Отправляем уведомление администраторам
            try:
                if site_settings.admin_notification_emails:
                    send_new_order_admin_notification(request, order)
            except Exception as e:
                print(f"Ошибка отправки уведомления админу: {e}")
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


# --- ЭТИ ФУНКЦИИ ОСТАЮТСЯ, НО ТЕПЕРЬ ОНИ ВЫЗЫВАЮТСЯ НАПРЯМУЮ ---
def send_order_confirmation_email(order):
    site_settings = SiteSettings.get_solo()
    subject = f'Подтверждение заказа #{order.id} - {site_settings.shop_name}'
    html_content = render_to_string('orders/email/customer_confirmation.html', {'order': order, 'site_settings': site_settings})
    text_content = f'Ваш заказ #{order.id} принят.'
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [order.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def send_new_order_admin_notification(request, order):
    site_settings = SiteSettings.get_solo()
    recipient_list = [email.strip() for email in site_settings.admin_notification_emails.split(',') if email.strip()]
    if not recipient_list:
        return
    subject = f'Новый заказ #{order.id} на сайте {site_settings.shop_name}'
    admin_order_url = request.build_absolute_uri(reverse('admin:orders_order_change', args=[order.id]))
    html_message = render_to_string('orders/email/admin_notification.html', {'order': order, 'admin_order_url': admin_order_url, 'site_settings': site_settings})
    text_content = f"Новый заказ #{order.id}. Ссылка: {admin_order_url}"
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, recipient_list)
    msg.attach_alternative(html_message, "text/html")
    msg.send()

def send_status_update_email(order):
    site_settings = SiteSettings.get_solo()
    subject = f'Статус вашего заказа #{order.id} изменен - {site_settings.shop_name}'
    html_content = render_to_string('orders/email/status_update.html', {'order': order, 'site_settings': site_settings})
    text_content = f'Статус вашего заказа #{order.id} изменен на "{order.get_status_display()}".'
    msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_HOST_USER, [order.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)