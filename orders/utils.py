# orders/utils.py

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from shop.models import SiteSettings


def send_cancellation_notification_to_admin(request, order):
    """
    Отправляет email-уведомление администраторам об отмене заказа.
    """
    site_settings = SiteSettings.get_solo()

    # Получаем список email'ов админов из настроек и очищаем его
    if site_settings.admin_notification_emails:
        admin_emails = [email.strip() for email in site_settings.admin_notification_emails.split(',') if email.strip()]
    else:
        admin_emails = []

    # Если email'ы не указаны, ничего не делаем
    if not admin_emails:
        print("Warning: Admin notification emails are not set. Cannot send cancellation email.")
        return

    # Формируем абсолютную ссылку на заказ в админ-панели
    admin_order_url = request.build_absolute_uri(
        reverse('admin:orders_order_change', args=[order.id])
    )

    subject = f'Заказ #{order.id} на сайте {site_settings.shop_name} был отменен клиентом'

    context = {
        'order': order,
        'admin_order_url': admin_order_url,
        'site_settings': site_settings,
    }

    html_message = render_to_string('orders/email/admin_cancellation_notification.html', context)

    try:
        send_mail(
            subject=subject,
            message='',  # Текстовая версия не нужна, т.к. мы отправляем HTML
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False  # Установите True, если не хотите, чтобы ошибка отправки ломала сайт
        )
    except Exception as e:
        # В реальном проекте здесь лучше использовать логирование
        print(f"Error sending cancellation email for order #{order.id}: {e}")