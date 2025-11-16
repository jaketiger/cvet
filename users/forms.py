# users/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from shop.models import Profile


class RegistrationForm(forms.ModelForm):
    # Определяем поля для паролей, чтобы они были доступны в форме
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'first_name')  # Фамилию убрали, но можно вернуть, если нужно

    # Мы будем добавлять классы и плейсхолдеры через виджеты, это чище
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'placeholder': 'ivanov@email.com'})
        self.fields['first_name'].widget.attrs.update({'placeholder': 'Иван'})

        # Применяем стили ко всем полям сразу
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_password2(self):
        cd = self.cleaned_data
        if cd.get('password') and cd.get('password2') and cd['password'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают.')
        return cd.get('password2')

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()  # Приводим email к нижнему регистру
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Устанавливаем пароль правильным, хешированным способом
        user.set_password(self.cleaned_data["password"])

        # Генерируем уникальный username из email
        email = self.cleaned_data['email']
        username_base = email.split('@')[0].replace('.', '').replace('-', '')  # Очищаем от лишних символов
        username = username_base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{username_base}{counter}"
            counter += 1
        user.username = username

        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    # Эта форма остается без изменений, но используем ваш вариант
    username = forms.EmailField(label="Email",
                                widget=forms.EmailInput(attrs={'autofocus': True, 'class': 'form-control'}))
    password = forms.CharField(label="Пароль", strip=False, widget=forms.PasswordInput(
        attrs={'autocomplete': 'current-password', 'class': 'form-control'}))


class UserEditForm(forms.ModelForm):
    # Эта форма остается без изменений
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileEditForm(forms.ModelForm):
    # Эта форма остается без изменений
    class Meta:
        model = Profile
        fields = ('phone', 'address', 'postal_code', 'city')