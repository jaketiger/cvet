# cart/forms.py

from django import forms

# Создаем список с вариантами количества от 1 до 20
PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 21)]

class CartAddProductForm(forms.Form):
    # coerce=int преобразует выбранное значение в целое число
    quantity = forms.TypedChoiceField(
        choices=PRODUCT_QUANTITY_CHOICES,
        coerce=int,
        label='Количество'
    )
    # Это скрытое поле, которое говорит, нужно ли перезаписать количество (True)
    # или просто добавить к существующему (False).
    update = forms.BooleanField(required=False, initial=False, widget=forms.HiddenInput)