# promo/forms.py

from django import forms

class PromoApplyForm(forms.Form):
    code = forms.CharField(
        label='Промокод',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите промокод'
        })
    )