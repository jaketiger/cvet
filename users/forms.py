# users/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Profile
from .utils import normalize_phone


class RegistrationForm(forms.ModelForm):
    """
    Форма регистрации.
    Используем ModelForm, чтобы вручную управлять полями и сохранением пароля.
    """
    email = forms.EmailField(
        label='Адрес email',
        required=False,
        help_text='Нужен для восстановления пароля и получения чеков.',
        widget=forms.EmailInput(attrs={
            'placeholder': 'ivanov@email.com (не обязательно)',
            'class': 'form-control'
        })
    )

    first_name = forms.CharField(
        label='Имя',
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Иван',
            'class': 'form-control'
        })
    )

    phone = forms.CharField(
        label='Номер телефона',
        required=True,
        help_text='Формат: +7 (999) 000-00-00',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (___) ___-__-__',
            'data-mask': 'phone'
        })
    )

    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    password2 = forms.CharField(
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('email', 'first_name')

    def clean_password(self):
        """Проверка сложности пароля стандартными валидаторами Django"""
        password = self.cleaned_data.get('password')
        if password:
            validate_password(password)
        return password

    def clean_password2(self):
        """Проверка совпадения паролей"""
        cd = self.cleaned_data
        if cd.get('password') and cd.get('password2') and cd['password'] != cd['password2']:
            raise ValidationError('Пароли не совпадают.')
        return cd.get('password2')

    def clean_email(self):
        """Проверка уникальности Email (если введен)"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower()
            if User.objects.filter(email=email).exists():
                raise ValidationError('Пользователь с таким email уже существует.')
            return email
        return ""

    def clean_phone(self):
        """Валидация и нормализация телефона"""
        raw_phone = self.cleaned_data.get('phone')
        norm_phone = normalize_phone(raw_phone)

        if not norm_phone or len(norm_phone) != 11:
            raise ValidationError('Введите корректный номер телефона (11 цифр).')

        if Profile.objects.filter(phone=norm_phone).exists():
            raise ValidationError('Этот номер телефона уже зарегистрирован.')

        return norm_phone

    def save(self, commit=True):
        """
        Сохранение пользователя.
        1. Создаем объект User.
        2. Хешируем пароль.
        3. Генерируем уникальный username.
        4. Сохраняем User.
        5. Создаем/Обновляем Profile с телефоном.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.first_name = self.cleaned_data['first_name']

        # ВАЖНО: Явно устанавливаем пароль (хеширование)
        user.set_password(self.cleaned_data['password'])

        # Логика генерации username (Django требует username, даже если мы входим по email)
        if user.email:
            username_base = user.email.split('@')[0]
        else:
            # Если email нет, берем телефон как основу
            username_base = normalize_phone(self.cleaned_data['phone'])

        # Очистка от спецсимволов
        if username_base:
            username_base = username_base.replace('.', '').replace('-', '').replace('+', '')
        else:
            username_base = 'user'

        # Обеспечение уникальности username
        username = username_base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{username_base}{counter}"
            counter += 1
        user.username = username

        if commit:
            user.save()
            # Сохраняем телефон в профиль
            if hasattr(user, 'profile'):
                user.profile.phone = self.cleaned_data['phone']
                user.profile.save()
            else:
                Profile.objects.create(user=user, phone=self.cleaned_data['phone'])

        return user


class LoginForm(AuthenticationForm):
    """Форма входа в систему"""
    username = forms.CharField(
        label="Email или номер телефона",
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'class': 'form-control',
            'placeholder': '+7... или email'
        })
    )
    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'class': 'form-control'
        })
    )


class UserEditForm(forms.ModelForm):
    """Форма редактирования основных данных пользователя (Имя, Email)"""

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


class ProfileEditForm(forms.ModelForm):
    """Форма редактирования профиля (Телефон, Адрес)"""

    class Meta:
        model = Profile
        fields = ('phone', 'address', 'postal_code', 'city')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

        # Маска для телефона
        self.fields['phone'].widget.attrs.update({
            'data-mask': 'phone',
            'placeholder': '+7 (___) ___-__-__'
        })

    def clean_phone(self):
        """Проверка телефона при редактировании (чтобы не занял чужой)"""
        raw_phone = self.cleaned_data.get('phone')
        norm_phone = normalize_phone(raw_phone)

        if not norm_phone:
            return None

        if len(norm_phone) != 11:
            raise ValidationError('Введите корректный номер телефона.')

        # Проверяем, не занят ли номер кем-то другим (исключая текущего пользователя)
        if Profile.objects.filter(phone=norm_phone).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Этот номер телефона уже занят другим пользователем.')

        return norm_phone