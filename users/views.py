# users/views.py

from django.shortcuts import render, redirect
from .forms import RegistrationForm
from django.contrib.auth import login
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.db.models.query_utils import Q
from django_q.tasks import async_task  # <--- ВАЖНЫЙ ИМПОРТ ДЛЯ АСИНХРОННОСТИ


def register(request):
    """
    Обрабатывает регистрацию нового пользователя и сразу выполняет вход.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # 1. Сохраняем пользователя
            user = form.save()

            # 2. АВТОМАТИЧЕСКИЙ ВХОД
            login(request, user, backend='users.backends.EmailOrPhoneBackend')

            # 3. Перенаправляем в личный кабинет
            return redirect('shop:cabinet')
    else:
        form = RegistrationForm()
    return render(request, 'users/register.html', {'form': form})


def password_reset_request(request):
    """
    Обрабатывает запрос на сброс пароля.
    Находит пользователя и запускает АСИНХРОННУЮ задачу отправки письма.
    """
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            associated_users = User.objects.filter(Q(email=email))

            if associated_users.exists():
                for user in associated_users:
                    # Определение протокола (http или https)
                    protocol = 'https' if request.is_secure() else 'http'
                    domain = request.get_host()

                    # === АСИНХРОННЫЙ ЗАПУСК ===
                    # Мы передаем только ID пользователя и параметры домена.
                    # Вся тяжелая работа (генерация токена, рендеринг, SMTP) будет в воркере.
                    async_task(
                        'users.utils.send_password_reset_email_task',
                        user_id=user.pk,
                        domain=domain,
                        protocol=protocol
                    )

                # Сразу перенаправляем пользователя, не дожидаясь отправки письма
                return redirect('password_reset_done')
    else:
        form = PasswordResetForm()

    return render(request=request, template_name="users/password_reset_form.html", context={"form": form})