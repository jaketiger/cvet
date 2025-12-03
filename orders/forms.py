# orders/forms.py

from django import forms
from django.utils import timezone
from .models import Order
from shop.models import Postcard, SiteSettings


# === ФОРМА ДЛЯ БЫСТРОГО ЗАКАЗА (1 Клик) ===
class OneClickOrderForm(forms.ModelForm):
    phone = forms.CharField(
        label='Ваш телефон',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (___) ___-__-__',
            'data-mask': 'phone'
        })
    )
    first_name = forms.CharField(
        label='Ваше имя',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Как к вам обращаться?'
        })
    )

    class Meta:
        model = Order
        fields = ['phone', 'first_name']


# === ОСНОВНАЯ ФОРМА ОФОРМЛЕНИЯ ЗАКАЗА ===
class OrderCreateForm(forms.ModelForm):
    delivery_option = forms.ChoiceField(
        label="Способ получения",
        choices=Order.DELIVERY_CHOICES,
        widget=forms.RadioSelect,
        initial='delivery'
    )

    # ЗАМЕНЯЕМ ModelChoiceField на CharField для обработки вручную
    postcard = forms.CharField(
        required=False,
        widget=forms.HiddenInput()  # Используем hidden input, так как у нас своя карусель
    )

    recipient_name = forms.CharField(required=False)
    recipient_phone = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = Order
        fields = [
            'delivery_option',
            'first_name', 'last_name', 'email', 'phone',
            'address', 'postal_code', 'city',
            'postcard_text', 'custom_postcard_image',
            'recipient_name', 'recipient_phone',
            'delivery_date', 'delivery_time'
        ]
        # УБИРАЕМ 'postcard' из fields, так как обрабатываем его отдельно
        widgets = {
            'delivery_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control datepicker-input',
                    'placeholder': 'Нажмите для выбора даты',
                    'autocomplete': 'off'
                }
            ),
            'delivery_time': forms.TextInput(attrs={'class': 'form-control'}),
            'postcard_text': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

        # Делаем поля адреса и времени необязательными
        self.fields['address'].required = False
        self.fields['city'].required = False
        self.fields['postal_code'].required = False
        self.fields['delivery_date'].required = False
        self.fields['delivery_time'].required = False

    def clean(self):
        cleaned_data = super().clean()
        delivery_option = cleaned_data.get('delivery_option')

        # Получаем "сырые" данные
        time_mode = self.data.get('time_mode')
        raw_postcard = self.data.get('postcard')

        # ОБРАБОТКА ОТКРЫТКИ ВРУЧНУЮ
        self.postcard_value = None  # Сохраняем объект Postcard здесь

        if raw_postcard == 'custom':
            # Кастомная открытка - postcard будет None
            self.postcard_value = None
        elif raw_postcard == '':
            # Без открытки
            self.postcard_value = None
            # Очищаем текст и фото
            cleaned_data['postcard_text'] = ''
            if 'custom_postcard_image' in self.files:
                del self.files['custom_postcard_image']
        elif raw_postcard:
            # Пытаемся получить объект Postcard
            try:
                postcard = Postcard.objects.get(id=int(raw_postcard))
                self.postcard_value = postcard
            except (ValueError, Postcard.DoesNotExist):
                self.add_error('postcard', 'Выбранная открытка не найдена')

        # Сохраняем raw значение в cleaned_data для дальнейшего использования
        cleaned_data['postcard_raw'] = raw_postcard

        # Заглушки для необязательных полей
        if not cleaned_data.get('last_name'):
            cleaned_data['last_name'] = '-'
        if not cleaned_data.get('email'):
            cleaned_data['email'] = 'no-email@provided.com'

        # === ВАЛИДАЦИЯ АДРЕСА ===
        if delivery_option == 'delivery':
            if not cleaned_data.get('address'):
                self.add_error('address', 'Укажите улицу и дом.')
            if not cleaned_data.get('city'):
                self.add_error('city', 'Укажите город.')
        else:
            # Если самовывоз - ставим заглушки
            if not cleaned_data.get('address'):
                cleaned_data['address'] = 'Самовывоз'
            if not cleaned_data.get('city'):
                cleaned_data['city'] = 'Самовывоз'
            if not cleaned_data.get('postal_code'):
                cleaned_data['postal_code'] = '000000'

        # === ВАЛИДАЦИЯ ВРЕМЕНИ (ASAP vs EXACT) ===
        if time_mode == 'asap':
            cleaned_data['delivery_time'] = 'asap'
            cleaned_data['delivery_date'] = timezone.now().date()
        else:
            if not cleaned_data.get('delivery_date'):
                self.add_error('delivery_date', 'Выберите дату получения.')
            d_time = cleaned_data.get('delivery_time')
            if not d_time:
                self.add_error('delivery_time', 'Выберите интервал времени.')

        # === ВАЛИДАЦИЯ КАСТОМНОЙ ОТКРЫТКИ ===
        if raw_postcard == 'custom' and not cleaned_data.get('custom_postcard_image'):
            # Предупреждение, но не ошибка
            pass

        # === ВАЛИДАЦИЯ ПОЛУЧАТЕЛЯ ===
        r_name = cleaned_data.get('recipient_name')
        r_phone = cleaned_data.get('recipient_phone')
        if r_name and not r_phone:
            self.add_error('recipient_phone', 'Укажите телефон получателя.')

        return cleaned_data

    def save(self, commit=True):
        # Переопределяем save, чтобы установить postcard вручную
        order = super().save(commit=False)

        # Устанавливаем postcard из сохраненного значения
        if hasattr(self, 'postcard_value'):
            order.postcard = self.postcard_value

        if commit:
            order.save()
            self.save_m2m()

        return order