# cart/forms.py
from django import forms

class CartAddProductForm(forms.Form):
    # ИЗМЕНЕНИЕ: Заменяем TypedChoiceField на IntegerField
    quantity = forms.IntegerField(
        min_value=1,
        max_value=999, # Вы можете установить любой разумный максимум или убрать его
        label='Количество',
        initial=1,
        # Указываем, что в HTML это должно быть <input type="number">
        # Также можно добавить стили для красоты
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 40px; text-align: center;'
        })
    )
    update = forms.BooleanField(required=False,
                                initial=False,
                                widget=forms.HiddenInput)