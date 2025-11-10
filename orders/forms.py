# orders/forms.py

from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    # Добавляем поле для выбора способа получения заказа
    delivery_option = forms.ChoiceField(
        label="Способ получения",
        choices=Order.DELIVERY_CHOICES,
        widget=forms.RadioSelect, # Используем радио-кнопки для наглядности
        initial='delivery' # Значение по умолчанию
    )

    class Meta:
        model = Order
        # Добавляем delivery_option в список полей
        fields = ['delivery_option', 'first_name', 'last_name', 'email', 'phone', 'address', 'postal_code', 'city']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Добавляем CSS-класс ко всем полям для стилизации
        for field in self.fields:
            if field != 'delivery_option': # Кроме радио-кнопок
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })