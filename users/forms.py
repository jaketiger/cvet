# users/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
import random


# --- НАЧАЛО КЛАССА ФОРМЫ РЕГИСТРАЦИИ ---
class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(label="Имя", max_length=150, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=150, required=True)
    email = forms.EmailField(label="Email", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'email',)

    # --- ПРАВИЛЬНОЕ МЕСТО ДЛЯ МЕТОДА ---
    # Этот метод находится на том же уровне, что и __init__ и save.
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "Этот email уже зарегистрирован. Пожалуйста, войдите или используйте другой email.")
        return email

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].label = "Пароль"
        self.fields['password1'].help_text = None

        self.fields['password2'].label = "Подтверждение пароля"
        self.fields['password2'].help_text = None

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name == 'first_name':
                field.widget.attrs['placeholder'] = 'Иван'
            elif field_name == 'last_name':
                field.widget.attrs['placeholder'] = 'Иванов'
            elif field_name == 'email':
                field.widget.attrs['placeholder'] = 'ivanov@email.com'

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email']
        username_base = email.split('@')[0]
        username = username_base

        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{username_base}{counter}"
            counter += 1

        user.username = username
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = email

        if commit:
            user.save()

        return user


# --- КОНЕЦ КЛАССА ФОРМЫ РЕГИСТРАЦИИ ---


# --- НАЧАЛО КЛАССА ФОРМЫ ВХОДА ---
class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True, 'class': 'form-control'})
    )

    password = forms.CharField(
        label="Пароль",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'}),
    )
# --- КОНЕЦ КЛАССА ФОРМЫ ВХОДА ---