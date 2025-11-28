# users/backends.py

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import Profile
from .utils import normalize_phone

User = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    """
    Авторизация по Email ИЛИ по Телефону.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            return None

        user = None

        # 1. Проверяем, похоже ли это на Email
        if '@' in username:
            try:
                user = User.objects.get(email__iexact=username)
            except User.DoesNotExist:
                pass

        # 2. Если не Email или не нашли, пробуем как Телефон
        if not user:
            clean_phone = normalize_phone(username)
            if clean_phone:
                try:
                    profile = Profile.objects.get(phone=clean_phone)
                    user = profile.user
                except Profile.DoesNotExist:
                    pass

        # 3. Если и телефона нет, пробуем как обычный username (на всякий случай)
        if not user:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        # Проверяем пароль
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None