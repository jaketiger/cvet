# orders/utils.py

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from shop.models import SiteSettings
from .models import Order


# ВАЖНО: Все функции теперь принимают простые типы данных (ID, строки),
# а не сложные объекты вроде 'request'.


def send_order_creation_emails_task(order_id, base_url):
    """
    Асинхронная ЗАДАЧА для отправки писем о СОЗДАНИИ заказа клиенту и админу.
    Вызывается из orders/views.py после создания заказа.
    """
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        print(f"Задача не выполнена: Заказ #{order_id} не найден.")
        return

    site_settings = SiteSettings.get_solo()
    context = {'order': order, 'site_settings': site_settings}

    # 1. Отправка письма клиенту
    subject_customer = f'Подтверждение заказа #{order.id} - {site_settings.shop_name}'
    html_content_customer = render_to_string('orders/email/customer_confirmation.html', context)
    msg_customer = EmailMultiAlternatives(subject_customer, '', settings.EMAIL_HOST_USER, [order.email])
    msg_customer.attach_alternative(html_content_customer, "text/html")
    msg_customer.send()

    # 2. Отправка письма админам
    admin_emails = [email.strip() for email in site_settings.admin_notification_emails.split(',') if email.strip()]
    if admin_emails:
        admin_order_url = f"{base_url}{reverse('admin:orders_order_change', args=[order.id])}"
        context_admin = {'order': order, 'site_settings': site_settings, 'admin_order_url': admin_order_url}
        subject_admin = f'Новый заказ #{order.id} на сайте {site_settings.shop_name}'
        html_content_admin = render_to_string('orders/email/admin_notification.html', context_admin)
        msg_admin = EmailMultiAlternatives(subject_admin, '', settings.EMAIL_HOST_USER, admin_emails)
        msg_admin.attach_alternative(html_content_admin, "text/html")
        msg_admin.send()


def send_cancellation_email_task(order_id, base_url):
    """
    Асинхронная ЗАДАЧА для уведомления админов об ОТМЕНЕ заказа клиентом.
    Вызывается из shop/views.py.
    """
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        print(f"Задача не выполнена: Заказ #{order_id} не найден.")
        return

    site_settings = SiteSettings.get_solo()
    admin_emails = [email.strip() for email in site_settings.admin_notification_emails.split(',') if email.strip()]
    if not admin_emails:
        return

    admin_order_url = f"{base_url}{reverse('admin:orders_order_change', args=[order.id])}"
    subject = f'Заказ #{order.id} на сайте {site_settings.shop_name} был отменен клиентом'
    context = {'order': order, 'admin_order_url': admin_order_url, 'site_settings': site_settings}
    html_message = render_to_string('orders/email/admin_cancellation_notification.html', context)

    msg = EmailMultiAlternatives(subject, '', settings.EMAIL_HOST_USER, admin_emails)
    msg.attach_alternative(html_message, "text/html")
    msg.send()


def send_status_update_email_task(order_id):
    """
    Асинхронная ЗАДАЧА для отправки письма клиенту об ИЗМЕНЕНИИ СТАТУСА заказа.
    Вызывается из orders/admin.py.
    """
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        print(f"Задача не выполнена: Заказ #{order_id} не найден.")
        return

    site_settings = SiteSettings.get_solo()
    subject = f'Статус вашего заказа #{order.id} изменен - {site_settings.shop_name}'
    context = {'order': order, 'site_settings': site_settings}
    html_content = render_to_string('orders/email/status_update.html', context)
    msg = EmailMultiAlternatives(subject, '', settings.EMAIL_HOST_USER, [order.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def send_order_confirmation_email_task(order_id):
    """
    Асинхронная ЗАДАЧА для повторной отправки ПОДТВЕРЖДЕНИЯ ЗАКАЗА только клиенту.
    Вызывается из кастомной кнопки в orders/admin.py.
    """
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        print(f"Задача не выполнена: Заказ #{order_id} не найден.")
        return

    site_settings = SiteSettings.get_solo()
    subject = f'Подтверждение заказа #{order.id} - {site_settings.shop_name}'
    context = {'order': order, 'site_settings': site_settings}
    html_content = render_to_string('orders/email/customer_confirmation.html', context)
    msg = EmailMultiAlternatives(subject, '', settings.EMAIL_HOST_USER, [order.email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()