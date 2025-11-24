# orders/forms.py

from django import forms
from .models import Order
from shop.models import Postcard


class OrderCreateForm(forms.ModelForm):
    # Поле доставки
    delivery_option = forms.ChoiceField(
        label="Способ получения",
        choices=Order.DELIVERY_CHOICES,
        widget=forms.RadioSelect,
        initial='delivery'
    )

    # Поле выбора открытки
    # Используем ModelChoiceField, но queryset определим в __init__,
    # чтобы избежать ошибки при старте сервера
    postcard = forms.ModelChoiceField(
        queryset=Postcard.objects.none(),  # Заглушка, переопределим ниже
        required=False,
        widget=forms.RadioSelect,
        label="Выберите открытку"
    )

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
            'postcard_text': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'Текст поздравления (напечатаем на обороте)...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Инициализация QuerySet для открыток (безопасно)
        try:
            self.fields['postcard'].queryset = Postcard.objects.filter(is_active=True)
        except:
            # Если таблица еще не создана (при миграциях), ставим пустой список
            self.fields['postcard'].queryset = Postcard.objects.none()

        # Добавляем CSS-класс ко всем полям, кроме радио
        for field in self.fields:
            if field not in ['delivery_option', 'postcard', 'custom_postcard_image']:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })