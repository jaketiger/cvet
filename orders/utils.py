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


#=====генератор интервалов=================================================================================

def get_work_hours(date_obj, settings, mode='delivery'):
    """
    Возвращает (start_time, end_time) для конкретной даты и режима (delivery/shop).
    """
    weekday = date_obj.weekday()  # 0=Пн, 6=Вс

    if mode == 'delivery':
        if weekday < 5:  # Пн-Пт
            return settings.delivery_weekdays_open, settings.delivery_weekdays_close
        else:  # Сб-Вс
            return settings.delivery_weekend_open, settings.delivery_weekend_close
    else:  # mode == 'shop' (pickup)
        if weekday < 5:
            return settings.work_weekdays_open, settings.work_weekdays_close
        else:
            return settings.work_weekend_open, settings.work_weekend_close


def generate_time_slots(date_str, mode='delivery'):
    """
    Генерирует список доступных интервалов.
    date_str: 'YYYY-MM-DD'
    mode: 'delivery' или 'pickup'
    """
    settings = SiteSettings.get_solo()
    tz = pytz.timezone(settings.site_time_zone)

    # 1. Парсим дату
    try:
        target_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return []

    # 2. Получаем текущее время в таймзоне магазина
    now_in_shop = timezone.now().astimezone(tz)
    today_date = now_in_shop.date()

    # Если запрошена прошедшая дата - интервалов нет
    if target_date < today_date:
        return []

    # 3. Получаем часы работы
    start_time, end_time = get_work_hours(target_date, settings, mode)

    # Превращаем в datetime для расчетов
    start_dt = tz.localize(datetime.datetime.combine(target_date, start_time))
    end_dt = tz.localize(datetime.datetime.combine(target_date, end_time))

    # Если закрытие меньше открытия (например, работает до 02:00 ночи следующего дня)
    if end_dt <= start_dt:
        end_dt += datetime.timedelta(days=1)

    slots = []
    current_dt = start_dt
    step = datetime.timedelta(minutes=settings.interval_step)  # 120 мин
    processing_delta = datetime.timedelta(minutes=settings.processing_time)  # 50 мин

    # 4. Цикл генерации
    while current_dt < end_dt:
        slot_end = current_dt + step

        # Если "хвостик" вылезает за время закрытия, обрезаем его
        if slot_end > end_dt:
            slot_end = end_dt

        # Проверяем длину последнего слота (не менее 30 мин, иначе нет смысла)
        if (slot_end - current_dt).total_seconds() < 1800:
            break

        # 5. ФИЛЬТРАЦИЯ (Если сегодня)
        is_available = True
        if target_date == today_date:
            # Условие: Начало интервала должно быть больше (Сейчас + Время на сборку)
            # Т.е. если сейчас 10:00, сборка 50 мин, то слоты начинающиеся раньше 10:50 скрываем.
            cutoff_time = now_in_shop + processing_delta

            if current_dt < cutoff_time:
                is_available = False

        if is_available:
            label = f"{current_dt.strftime('%H:%M')} - {slot_end.strftime('%H:%M')}"
            value = label  # То, что запишется в базу
            slots.append({'value': value, 'label': label})

        current_dt = slot_end

    return slots


def is_shop_open_now(mode='delivery'):
    """
    Проверяет, можно ли заказать 'Как можно быстрее' прямо сейчас.
    Возвращает: (bool is_open, str reason)
    """
    settings = SiteSettings.get_solo()
    tz = pytz.timezone(settings.site_time_zone)
    now = timezone.now().astimezone(tz)
    today = now.date()

    start_time, end_time = get_work_hours(today, settings, mode)

    start_dt = tz.localize(datetime.datetime.combine(today, start_time))
    end_dt = tz.localize(datetime.datetime.combine(today, end_time))

    # Проверка на ночное время работы
    if end_dt <= start_dt:
        end_dt += datetime.timedelta(days=1)

    # Условие закрытия (за 20 минут)
    cutoff_dt = end_dt - datetime.timedelta(minutes=settings.close_cutoff)

    if now < start_dt:
        return False, f"Откроемся в {start_time.strftime('%H:%M')}"

    if now >= cutoff_dt:
        return False, "Скоро закрытие"

    return True, ""

#===============================================================================================


def activate_site_timezone(site_settings):
    """
    Вспомогательная функция для активации часового пояса из настроек.
    """
    if site_settings.site_time_zone:
        try:
            timezone.activate(pytz.timezone(site_settings.site_time_zone))
        except Exception:
            timezone.deactivate()


def send_order_creation_emails_task(order_id, base_url):
    """
    Асинхронная задача: отправка писем о СОЗДАНИИ заказа (Клиенту + Админу).
    """
    print(f"--- НАЧАЛО ОТПРАВКИ (Заказ #{order_id}) ---")  # ЛОГ
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        print(f"Ошибка: Заказ {order_id} не найден.")
        return

    site_settings = SiteSettings.get_solo()
    activate_site_timezone(site_settings)

    try:
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
        # Заменяем ; на , (частая ошибка) и удаляем пробелы
        raw_emails = site_settings.admin_notification_emails.replace(';', ',')
        admin_emails = [email.strip() for email in raw_emails.split(',') if email.strip() and '@' in email]

        print(f"Email админов из настроек: {admin_emails}")  # ЛОГ

        if admin_emails:
            try:
                admin_order_url = f"{base_url}{reverse('admin:orders_order_change', args=[order.id])}"
                context_admin = context.copy()
                context_admin['admin_order_url'] = admin_order_url

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
    """
    Уведомление админа об ОТМЕНЕ заказа.
    """
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
    """
    Уведомление клиента об ИЗМЕНЕНИИ СТАТУСА.
    """
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
    """
    Повторная отправка (ручная).
    """
    try:
        order = Order.objects.get(id=order_id)
        if not order.email or 'no-email' in order.email: return

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