# orders/forms.py

from django import forms
from .models import Order
from shop.models import Postcard


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

    # Явно указываем, что эти поля не обязательны для проверки Django
    recipient_name = forms.CharField(required=False)
    recipient_phone = forms.CharField(required=False)
    last_name = forms.CharField(required=False)  # <--- ВАЖНО: Фамилия теперь не обязательна
    email = forms.EmailField(required=False)  # <--- ВАЖНО: Email тоже (если вдруг пустой)

    class Meta:
        model = Order
        fields = [
            'delivery_option',
            'first_name', 'last_name', 'email', 'phone',
            'address', 'postal_code', 'city',
            'postcard', 'postcard_text', 'custom_postcard_image',
            'recipient_name', 'recipient_phone'
        ]
        widgets = {
            'postcard_text': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            self.fields['postcard'].queryset = Postcard.objects.filter(is_active=True)
        except:
            pass

        # Отключаем обязательность адреса (проверим вручную)
        self.fields['address'].required = False
        self.fields['city'].required = False
        self.fields['postal_code'].required = False

        for field in self.fields:
            if field not in ['delivery_option', 'postcard', 'custom_postcard_image']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        delivery_option = cleaned_data.get('delivery_option')

        # 1. Заполняем пропуски (чтобы база не ругалась на NOT NULL)
        if not cleaned_data.get('last_name'):
            cleaned_data['last_name'] = '-'

        if not cleaned_data.get('email'):
            # Если email не введен, генерируем фейковый или берем из юзера во view
            cleaned_data['email'] = 'no-email@provided.com'

        # 2. Логика доставки
        if delivery_option == 'delivery':
            if not cleaned_data.get('address'):
                self.add_error('address', 'Укажите улицу и дом.')
            if not cleaned_data.get('city'):
                self.add_error('city', 'Укажите город.')
        else:
            # Для самовывоза ставим заглушки
            if not cleaned_data.get('address'):
                cleaned_data['address'] = 'Самовывоз'
            if not cleaned_data.get('city'):
                cleaned_data['city'] = 'Самовывоз'
            if not cleaned_data.get('postal_code'):
                cleaned_data['postal_code'] = '000000'

        # 3. Логика получателя
        r_name = cleaned_data.get('recipient_name')
        r_phone = cleaned_data.get('recipient_phone')
        # Если начали вводить имя получателя, требуем телефон
        if r_name and not r_phone:
            self.add_error('recipient_phone', 'Укажите телефон получателя.')

        return cleaned_data