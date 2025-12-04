# orders/utils.py

import pytz
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings
from shop.models import SiteSettings
from .models import Order
import datetime
from decimal import Decimal


# =====генератор интервалов=================================================================================

def get_work_hours(date_obj, settings, mode='delivery'):
    weekday = date_obj.weekday()

    if mode == 'delivery':
        if weekday < 5:
            return settings.delivery_weekdays_open, settings.delivery_weekdays_close
        else:
            return settings.delivery_weekend_open, settings.delivery_weekend_close
    else:
        if weekday < 5:
            return settings.work_weekdays_open, settings.work_weekdays_close
        else:
            return settings.work_weekend_open, settings.work_weekend_close


def generate_time_slots(date_str, mode='delivery'):
    settings = SiteSettings.get_solo()
    tz = pytz.timezone(settings.site_time_zone)

    try:
        target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return []

    now_in_shop = timezone.now().astimezone(tz)
    today_date = now_in_shop.date()

    if target_date < today_date:
        return []

    start_time, end_time = get_work_hours(target_date, settings, mode)

    start_dt = tz.localize(datetime.datetime.combine(target_date, start_time))
    end_dt = tz.localize(datetime.datetime.combine(target_date, end_time))

    if end_dt <= start_dt:
        end_dt += datetime.timedelta(days=1)

    slots = []
    current_dt = start_dt
    step = datetime.timedelta(minutes=settings.interval_step)
    processing_delta = datetime.timedelta(minutes=settings.processing_time)

    while current_dt < end_dt:
        slot_end = current_dt + step

        if slot_end > end_dt:
            slot_end = end_dt

        if (slot_end - current_dt).total_seconds() < 1800:
            break

        is_available = True
        if target_date == today_date:
            cutoff_time = now_in_shop + processing_delta
            if current_dt < cutoff_time:
                is_available = False

        if is_available:
            label = f"{current_dt.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
            value = label
            slots.append({'value': value, 'label': label})

        current_dt = slot_end

    return slots


def is_shop_open_now(mode='delivery'):
    settings = SiteSettings.get_solo()
    tz = pytz.timezone(settings.site_time_zone)
    now = timezone.now().astimezone(tz)
    today = now.date()

    start_time, end_time = get_work_hours(today, settings, mode)

    start_dt = tz.localize(datetime.datetime.combine(today, start_time))
    end_dt = tz.localize(datetime.datetime.combine(today, end_time))

    if end_dt <= start_dt:
        end_dt += datetime.timedelta(days=1)

    cutoff_dt = end_dt - datetime.timedelta(minutes=settings.close_cutoff)

    if now < start_dt:
        return False, f"Откроемся в {start_time.strftime('%H:%M')}"

    if now >= cutoff_dt:
        return False, "Скоро закрытие"

    return True, ""


# ===============================================================================================


def activate_site_timezone(site_settings):
    if site_settings.site_time_zone:
        try:
            timezone.activate(pytz.timezone(site_settings.site_time_zone))
        except Exception:
            timezone.deactivate()


def format_delivery_time(order):
    """ИСПРАВЛЕНО ДОБАВЛЕНО: Форматирует время доставки для отображения"""
    if order.delivery_time == 'asap':
        return 'Как можно быстрее'
    return order.delivery_time


def get_order_summary(order):
    """ИСПРАВЛЕНО ДОБАВЛЕНО: Возвращает сводку по заказу с правильным учетом открытки"""
    summary = {
        'items_cost': order.get_items_cost(),
        'discount': order.get_discount_amount(),
        'delivery_cost': order.delivery_cost,
        'postcard_cost': Decimal('0.00'),
        'total': order.get_total_cost(),
        'postcard_info': None
    }

    # ИСПРАВЛЕНО: Правильный расчет стоимости открытки
    if order.custom_postcard_image:
        summary['postcard_info'] = {
            'type': 'custom',
            'title': 'Свое фото',
            'price': order.postcard.price if order.postcard else Decimal('0.00')
        }
        summary['postcard_cost'] = order.postcard.price if order.postcard else Decimal('0.00')
    elif order.postcard:
        summary['postcard_info'] = {
            'type': 'catalog',
            'title': order.postcard.title,
            'price': order.postcard.price
        }
        summary['postcard_cost'] = order.postcard.price

    return summary


def send_order_creation_emails_task(order_id, base_url):
    print(f"--- НАЧАЛО ОТПРАВКИ (Заказ #{order_id}) ---")
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        print(f"Ошибка: Заказ {order_id} не найден.")
        return

    site_settings = SiteSettings.get_solo()
    activate_site_timezone(site_settings)

    try:
        # ИСПРАВЛЕНО: Добавляем форматирование времени доставки
        order.delivery_time_display = format_delivery_time(order)

        context = {
            'order': order,
            'site_settings': site_settings,
            'base_url': base_url
        }

        # 1. КЛИЕНТУ
        if order.email and 'no-email' not in order.email:
            try:
                subject_customer = f'Подтверждение заказа #{order.id} - {site_settings.shop_name}'
                html_content_customer = render_to_string('orders/email/customer_confirmation.html', context)
                msg_customer = EmailMultiAlternatives(subject_customer, '', settings.EMAIL_HOST_USER, [order.email])
                msg_customer.attach_alternative(html_content_customer, "text/html")
                msg_customer.send()
                print(f"✅ Клиенту ({order.email}) отправлено.")
            except Exception as e:
                print(f"❌ Ошибка отправки клиенту: {e}")

        # 2. АДМИНАМ
        raw_emails = site_settings.admin_notification_emails.replace(';', ',')
        admin_emails = [email.strip() for email in raw_emails.split(',') if email.strip() and '@' in email]

        print(f"Email админов из настроек: {admin_emails}")

        if admin_emails:
            try:
                admin_order_url = f"{base_url}{reverse('admin:orders_order_change', args=[order.id])}"
                context_admin = context.copy()
                context_admin['admin_order_url'] = admin_order_url

                # ИСПРАВЛЕНО: В заголовке теперь правильная общая стоимость
                subject_admin = f'Новый заказ #{order.id} ({order.get_total_cost()} руб.)'
                html_content_admin = render_to_string('orders/email/admin_notification.html', context_admin)

                msg_admin = EmailMultiAlternatives(subject_admin, '', settings.EMAIL_HOST_USER, admin_emails)
                msg_admin.attach_alternative(html_content_admin, "text/html")
                msg_admin.send()
                print(f"✅ Админам отправлено.")
            except Exception as e:
                print(f"❌ Ошибка отправки админу: {e}")
        else:
            print("⚠️ Список админов пуст! Проверьте 'Настройки сайта' -> 'Email для уведомлений'")

    except Exception as e:
        print(f"❌ Общая ошибка в задаче: {e}")
    finally:
        timezone.deactivate()
        print("--- КОНЕЦ ---")


def send_cancellation_email_task(order_id, base_url):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return

    site_settings = SiteSettings.get_solo()
    activate_site_timezone(site_settings)

    try:
        raw_emails = site_settings.admin_notification_emails.replace(';', ',')
        admin_emails = [email.strip() for email in raw_emails.split(',') if email.strip() and '@' in email]

        if admin_emails:
            admin_order_url = f"{base_url}{reverse('admin:orders_order_change', args=[order.id])}"
            subject = f'ОТМЕНА: Заказ #{order.id} на сайте {site_settings.shop_name}'

            context = {
                'order': order,
                'admin_order_url': admin_order_url,
                'site_settings': site_settings,
                'base_url': base_url
            }

            html_message = render_to_string('orders/email/admin_cancellation_notification.html', context)

            msg = EmailMultiAlternatives(subject, '', settings.EMAIL_HOST_USER, admin_emails)
            msg.attach_alternative(html_message, "text/html")
            msg.send()
            print("✅ Письмо об отмене отправлено админу.")
        else:
            print("⚠️ Нет email админов для уведомления об отмене.")

    except Exception as e:
        print(f"Ошибка при отправке отмены: {e}")
    finally:
        timezone.deactivate()


def send_status_update_email_task(order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return

    if not order.email or 'no-email' in order.email:
        return

    site_settings = SiteSettings.get_solo()
    activate_site_timezone(site_settings)

    try:
        subject = f'Статус заказа #{order.id} изменен - {site_settings.shop_name}'
        context = {'order': order, 'site_settings': site_settings}

        html_content = render_to_string('orders/email/status_update.html', context)
        msg = EmailMultiAlternatives(subject, '', settings.EMAIL_HOST_USER, [order.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        print(f"Ошибка при отправке статуса: {e}")
    finally:
        timezone.deactivate()


def send_order_confirmation_email_task(order_id):
    try:
        order = Order.objects.get(id=order_id)
        if not order.email or 'no-email' in order.email:
            return

        site_settings = SiteSettings.get_solo()
        activate_site_timezone(site_settings)

        subject = f'Подтверждение заказа #{order.id} - {site_settings.shop_name}'
        context = {'order': order, 'site_settings': site_settings}

        html_content = render_to_string('orders/email/customer_confirmation.html', context)
        msg = EmailMultiAlternatives(subject, '', settings.EMAIL_HOST_USER, [order.email])
        msg.attach_alternative(html_content, "text/html")
        msg.send()
    except Exception as e:
        print(f"Ошибка при повторной отправке: {e}")
    finally:
        timezone.deactivate()