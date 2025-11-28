# orders/forms.py

from django import forms
from .models import Order
from shop.models import Postcard


# === НОВАЯ ФОРМА ДЛЯ 1 КЛИКА ===
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


# ===============================

class OrderCreateForm(forms.ModelForm):
    delivery_option = forms.ChoiceField(
        label="Способ получения",
        choices=Order.DELIVERY_CHOICES,
        widget=forms.RadioSelect,
        initial='delivery'
    )

    postcard = forms.ModelChoiceField(
        queryset=Postcard.objects.none(),
        required=False,
        widget=forms.RadioSelect
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
            'postcard', 'postcard_text', 'custom_postcard_image',
            'recipient_name', 'recipient_phone',
            'delivery_date', 'delivery_time'
        ]
        widgets = {
            'delivery_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control datepicker-input',
                    'placeholder': 'Нажмите для выбора даты',
                    'autocomplete': 'off'
                }
            ),
            'delivery_time': forms.Select(attrs={'class': 'form-control'}),
            'postcard_text': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

        try:
            self.fields['postcard'].queryset = Postcard.objects.filter(is_active=True)
        except:
            pass

        self.fields['address'].required = False
        self.fields['city'].required = False
        self.fields['postal_code'].required = False
        self.fields['delivery_date'].required = False
        self.fields['delivery_time'].required = False

    def clean(self):
        cleaned_data = super().clean()
        delivery_option = cleaned_data.get('delivery_option')

        if not cleaned_data.get('last_name'):
            cleaned_data['last_name'] = '-'
        if not cleaned_data.get('email'):
            cleaned_data['email'] = 'no-email@provided.com'

        if delivery_option == 'delivery':
            if not cleaned_data.get('address'):
                self.add_error('address', 'Укажите улицу и дом.')
            if not cleaned_data.get('city'):
                self.add_error('city', 'Укажите город.')
            if not cleaned_data.get('delivery_date'):
                self.add_error('delivery_date', 'Выберите дату доставки.')
            if not cleaned_data.get('delivery_time'):
                self.add_error('delivery_time', 'Выберите время доставки.')
        else:
            if not cleaned_data.get('address'):
                cleaned_data['address'] = 'Самовывоз'
            if not cleaned_data.get('city'):
                cleaned_data['city'] = 'Самовывоз'
            if not cleaned_data.get('postal_code'):
                cleaned_data['postal_code'] = '000000'

        r_name = cleaned_data.get('recipient_name')
        r_phone = cleaned_data.get('recipient_phone')
        if r_name and not r_phone:
            self.add_error('recipient_phone', 'Укажите телефон получателя.')

        return cleaned_data