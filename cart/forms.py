# cart/forms.py
from django import forms


class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=999,
        label='Количество',
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'style': 'width: 50px; text-align: center;'
        })
    )
    update = forms.BooleanField(required=False,
                                initial=False,
                                widget=forms.HiddenInput)

    # --- НОВОЕ ПОЛЕ ДЛЯ ТЕКСТА ОТКРЫТКИ ---
    postcard_text = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Текст поздравления...',
            'class': 'postcard-input'
        }),
        label="Текст открытки"
    )