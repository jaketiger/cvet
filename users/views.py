# users/views.py

from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.urls import reverse
# --- НОВЫЙ ИМПОРТ ---
from shop.models import SiteSettings


def register(request):
    """
    Обрабатывает регистрацию нового пользователя.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'users/register.html', {'form': form})


def password_reset_request(request):
    """
    Обрабатывает запрос на сброс пароля. Находит пользователя по email
    и отправляет ему письмо со ссылкой для сброса.
    """
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=email))
            if associated_users.exists():
                for user in associated_users:
                    # --- ИЗМЕНЕНИЕ: Теперь SiteSettings импортирован ---
                    site_settings = SiteSettings.get_solo()
                    subject = f"Сброс пароля на сайте {site_settings.shop_name}"

                    context = {
                        "email": user.email,
                        'domain': request.get_host(),
                        'site_name': site_settings.shop_name,
                        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                        "user": user,
                        'token': default_token_generator.make_token(user),
                        'protocol': 'http',
                        'site_settings': site_settings  # <-- Передаем в шаблон
                    }

                    html_content = render_to_string("registration/password_reset_email.html", context)
                    text_content = render_to_string("registration/password_reset_subject.txt", context)

                    msg = EmailMultiAlternatives(
                        subject,
                        text_content,
                        settings.EMAIL_HOST_USER,
                        [user.email]
                    )
                    msg.attach_alternative(html_content, "text/html")
                    msg.send(fail_silently=False)

                return redirect('password_reset_done')
    else:
        form = PasswordResetForm()

    return render(request=request, template_name="registration/password_reset_form.html", context={"form": form})