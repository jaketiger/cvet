# users/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField("Телефон", max_length=20, blank=True, null=True, unique=True)
    address = models.CharField("Адрес", max_length=250, blank=True)
    postal_code = models.CharField("Индекс", max_length=20, blank=True)
    city = models.CharField("Город", max_length=100, blank=True)

    def __str__(self):
        return f'Профиль {self.user.username}'

# --- ДОБАВИТЬ ЭТОТ БЛОК В КОНЕЦ ФАЙЛА ---
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Проверяем, есть ли профиль, и сохраняем.
    # Если профиля нет (для старых юзеров), создаем его.
    if not hasattr(instance, 'profile'):
        Profile.objects.create(user=instance)
    else:
        instance.profile.save()