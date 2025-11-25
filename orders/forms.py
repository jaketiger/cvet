# orders/forms.py

from django import forms
from .models import Order
from shop.models import Postcard


class OrderCreateForm(forms.ModelForm):
    # Доставка
    delivery_option = forms.ChoiceField(
        label="Способ получения",
        choices=Order.DELIVERY_CHOICES,
        widget=forms.RadioSelect,
        initial='delivery'
    )

    # Открытка (пустой queryset, заполним в __init__)
    postcard = forms.ModelChoiceField(
        queryset=Postcard.objects.none(),
        required=False,
        widget=forms.RadioSelect,
        label="Выберите открытку"
    )

    # Получатель (необязательные поля, проверим вручную)
    recipient_name = forms.CharField(required=False, label="Имя получателя")
    recipient_phone = forms.CharField(required=False, label="Телефон получателя")

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
            'postcard_text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Текст поздравления...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Загружаем открытки
        try:
            self.fields['postcard'].queryset = Postcard.objects.filter(is_active=True)
        except:
            pass

        # Делаем поля адреса необязательными на уровне формы
        # (Проверять их будем в clean, в зависимости от выбора доставки)
        self.fields['address'].required = False
        self.fields['city'].required = False
        self.fields['postal_code'].required = False

        # CSS классы
        for field in self.fields:
            if field not in ['delivery_option', 'postcard', 'custom_postcard_image']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        delivery_option = cleaned_data.get('delivery_option')

        # 1. ЛОГИКА АДРЕСА
        if delivery_option == 'delivery':
            # Если доставка — адрес обязателен
            if not cleaned_data.get('address'):
                self.add_error('address', 'Укажите адрес доставки.')
            if not cleaned_data.get('city'):
                self.add_error('city', 'Укажите город.')
        else:
            # Если самовывоз — очищаем адрес или ставим прочерк, чтобы база не ругалась
            if not cleaned_data.get('address'):
                cleaned_data['address'] = 'Самовывоз'
            if not cleaned_data.get('city'):
                cleaned_data['city'] = '-'
            if not cleaned_data.get('postal_code'):
                cleaned_data['postal_code'] = '-'

        # 2. ЛОГИКА ПОЛУЧАТЕЛЯ
        # Мы проверяем наличие имени получателя, только если оно было заполнено в форме.
        # В HTML мы используем radio (recipient_who), но в форму оно не передается напрямую.
        # Просто проверим: если заполнено имя получателя, должен быть и телефон.
        r_name = cleaned_data.get('recipient_name')
        r_phone = cleaned_data.get('recipient_phone')

        if r_name and not r_phone:
            self.add_error('recipient_phone', 'Укажите телефон получателя.')

        return cleaned_data