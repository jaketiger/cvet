# users/utils.py

import re
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from shop.models import SiteSettings


def normalize_phone(phone):
    """
    Приводит номер к формату 79991112233.
    Если номер невалидный, возвращает None.
    """
    if not phone:
        return None

    # Оставляем только цифры
    digits = re.sub(r'\D', '', phone)

    # Проверка длины и первой цифры для РФ (11 цифр, начинается с 7 или 8)
    if len(digits) == 11:
        if digits.startswith('8'):
            return '7' + digits[1:]  # Меняем 8 на 7
        elif digits.startswith('7'):
            return digits

    # Если вдруг номер 10 цифр (забыли +7), добавляем 7
    elif len(digits) == 10:
        return '7' + digits

    # Если формат совсем не тот, возвращаем как есть (пусть валидатор формы ругается)
    # или None, если хотим строгую проверку.
    return digits


def send_password_reset_email_task(user_id, domain, protocol):
    """
    Асинхронная задача для отправки письма сброса пароля.
    Запускается через django_q.
    """
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        # Если пользователя нет, ничего не делаем
        return

    site_settings = SiteSettings.get_solo()
    subject = f"Сброс пароля на сайте {site_settings.shop_name}"

    context = {
        "email": user.email,
        'domain': domain,
        'site_name': site_settings.shop_name,
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "user": user,
        'token': default_token_generator.make_token(user),
        'protocol': protocol,
        'site_settings': site_settings
    }

    # Рендеринг шаблонов
    # Обратите внимание: пути указывают на папку users/, куда мы перенесли шаблоны
    html_content = render_to_string("users/password_reset_email.html", context)
    text_content = render_to_string("users/password_reset_subject.txt", context)

    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.EMAIL_HOST_USER,
        [user.email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send(fail_silently=False)