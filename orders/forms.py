# orders/forms.py

from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone', 'address', 'postal_code', 'city']

    # ДОБАВЬТЕ ЭТОТ МЕТОД
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Этот цикл пройдет по всем полям формы...
        for field in self.fields:
            # ... и добавит к каждому полю ввода CSS-класс 'form-control'
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })