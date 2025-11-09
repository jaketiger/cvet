# users/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class EmailBackend(ModelBackend):
    """
    Кастомный бэкенд аутентификации.
    Позволяет пользователям входить, используя свой email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Пытаемся найти пользователя по email.
            # username здесь - это то, что пользователь ввел в поле логина.
            user = User.objects.get(email__iexact=username)
            # Проверяем пароль
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            # Если пользователь не найден, ничего не делаем,
            # чтобы Django мог проверить другие бэкенды (например, стандартный).
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None