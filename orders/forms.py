# orders/forms.py

from django import forms
from django.utils import timezone
from .models import Order
from shop.models import Postcard, SiteSettings
from decimal import Decimal


# === ФОРМА ДЛЯ БЫСТРОГО ЗАКАЗА (1 Клик) ===
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


# === ОСНОВНАЯ ФОРМА ОФОРМЛЕНИЯ ЗАКАЗА ===
class OrderCreateForm(forms.ModelForm):
    delivery_option = forms.ChoiceField(
        label="Способ получения",
        choices=Order.DELIVERY_CHOICES,
        widget=forms.RadioSelect,
        initial='delivery'
    )

    # ЗАМЕНЯЕМ ModelChoiceField на CharField для обработки вручную
    postcard = forms.CharField(
        required=False,
        widget=forms.HiddenInput()  # Используем hidden input, так как у нас своя карусель
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
            'postcard_text', 'custom_postcard_image',
            'recipient_name', 'recipient_phone',
            'delivery_date', 'delivery_time'
        ]
        # УБИРАЕМ 'postcard' из fields, так как обрабатываем его отдельно
        widgets = {
            'delivery_date': forms.DateInput(
                format='%Y-%m-%d',
                attrs={
                    'class': 'form-control datepicker-input',
                    'placeholder': 'Нажмите для выбора даты',
                    'autocomplete': 'off'
                }
            ),
            'delivery_time': forms.TextInput(attrs={'class': 'form-control'}),
            'postcard_text': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

        # Делаем поля адреса и времени необязательными
        self.fields['address'].required = False
        self.fields['city'].required = False
        self.fields['postal_code'].required = False
        self.fields['delivery_date'].required = False
        self.fields['delivery_time'].required = False

    def clean(self):
        cleaned_data = super().clean()
        delivery_option = cleaned_data.get('delivery_option')

        # Получаем "сырые" данные
        time_mode = self.data.get('time_mode')
        raw_postcard = self.data.get('postcard')

        # ИСПРАВЛЕНО: Также получаем ID для кастомной открытки
        selected_for_custom = self.data.get('selected_postcard_for_custom', '')
        postcard_id_for_custom = self.data.get('postcard_id_for_custom', '')

        print(f"DEBUG forms.py clean: raw_postcard = {raw_postcard}")
        print(f"DEBUG forms.py clean: selected_for_custom = {selected_for_custom}")
        print(f"DEBUG forms.py clean: postcard_id_for_custom = {postcard_id_for_custom}")

        # ОБРАБОТКА ОТКРЫТКИ ВРУЧНУЮ
        self.postcard_value = None  # Сохраняем объект Postcard здесь
        self.postcard_price = Decimal('0.00')  # ИСПРАВЛЕНО: Сохраняем цену

        # ИСПРАВЛЕНО: Правильная логика обработки открытки
        if raw_postcard == 'custom':
            # Кастомная открытка
            print("DEBUG forms.py: Обработка кастомной открытки")

            # ИСПРАВЛЕНО: Для кастомной открытки с фото всегда берем цену из настроек сайта
            try:
                site_settings = SiteSettings.get_solo()
                custom_price = site_settings.custom_postcard_price or Decimal('0.00')
                self.postcard_price = custom_price
                print(f"DEBUG forms.py: Цена кастомной открытки из настроек сайта: {custom_price}")

                # ИСПРАВЛЕНО: Проверяем, есть ли ID платной открытки для комбинации
                postcard_id = selected_for_custom or postcard_id_for_custom
                if postcard_id and postcard_id != '':
                    try:
                        postcard = Postcard.objects.get(id=int(postcard_id))
                        self.postcard_value = postcard
                        # Если есть платная основа, добавляем её цену
                        if postcard.price and postcard.price > 0:
                            self.postcard_price += postcard.price
                            print(f"DEBUG forms.py: + цена основы {postcard.price} = итого {self.postcard_price}")
                    except (ValueError, Postcard.DoesNotExist) as e:
                        print(f"DEBUG forms.py: Платная открытка не найдена: {e}")
                        self.postcard_value = None
            except Exception as e:
                print(f"DEBUG forms.py: Ошибка получения настроек сайта: {e}")
                self.postcard_price = Decimal('100.00')  # значение по умолчанию

        elif raw_postcard == '':
            # Без открытки
            self.postcard_value = None
            self.postcard_price = Decimal('0.00')
            print("DEBUG forms.py: Без открытки")
            # Очищаем текст и фото
            cleaned_data['postcard_text'] = ''
            if 'custom_postcard_image' in self.files:
                del self.files['custom_postcard_image']
        elif raw_postcard:
            # Пытаемся получить объект Postcard
            try:
                postcard = Postcard.objects.get(id=int(raw_postcard))
                self.postcard_value = postcard
                self.postcard_price = postcard.price
                print(f"DEBUG forms.py: Найдена обычная открытка: {postcard.title}, цена: {postcard.price}")
            except (ValueError, Postcard.DoesNotExist):
                self.add_error('postcard', 'Выбранная открытка не найдена')
                print(f"DEBUG forms.py: Открытка не найдена: {raw_postcard}")

        # Сохраняем raw значение в cleaned_data для дальнейшего использования
        cleaned_data['postcard_raw'] = raw_postcard
        cleaned_data['selected_for_custom'] = selected_for_custom

        # Заглушки для необязательных полей
        if not cleaned_data.get('last_name'):
            cleaned_data['last_name'] = '-'
        if not cleaned_data.get('email'):
            cleaned_data['email'] = 'no-email@provided.com'

        # === ВАЛИДАЦИЯ АДРЕСА ===
        if delivery_option == 'delivery':
            if not cleaned_data.get('address'):
                self.add_error('address', 'Укажите улицу и дом.')
            if not cleaned_data.get('city'):
                self.add_error('city', 'Укажите город.')
        else:
            # Если самовывоз - ставим заглушки
            if not cleaned_data.get('address'):
                cleaned_data['address'] = 'Самовывоз'
            if not cleaned_data.get('city'):
                cleaned_data['city'] = 'Самовывоз'
            if not cleaned_data.get('postal_code'):
                cleaned_data['postal_code'] = '000000'

        # === ВАЛИДАЦИЯ ВРЕМЕНИ (ASAP vs EXACT) ===
        if time_mode == 'asap':
            cleaned_data['delivery_time'] = 'asap'
            cleaned_data['delivery_date'] = timezone.now().date()
        else:
            if not cleaned_data.get('delivery_date'):
                self.add_error('delivery_date', 'Выберите дату получения.')
            d_time = cleaned_data.get('delivery_time')
            if not d_time:
                self.add_error('delivery_time', 'Выберите интервал времени.')

        # === ВАЛИДАЦИЯ КАСТОМНОЙ ОТКРЫТКИ ===
        if raw_postcard == 'custom' and not cleaned_data.get('custom_postcard_image'):
            # Предупреждение, но не ошибка (можно загрузить позже или использовать без фото)
            print("DEBUG forms.py: Кастомная открытка без загруженного фото")

        # === ВАЛИДАЦИЯ ПОЛУЧАТЕЛЯ ===
        r_name = cleaned_data.get('recipient_name')
        r_phone = cleaned_data.get('recipient_phone')
        if r_name and not r_phone:
            self.add_error('recipient_phone', 'Укажите телефон получателя.')

        return cleaned_data

    def save(self, commit=True):
        # Переопределяем save, чтобы установить postcard вручную
        order = super().save(commit=False)

        # ИСПРАВЛЕНО: Устанавливаем postcard и его цену
        if hasattr(self, 'postcard_value'):
            order.postcard = self.postcard_value

        # ИСПРАВЛЕНО: Всегда устанавливаем финальную цену из postcard_price
        if hasattr(self, 'postcard_price'):
            order.postcard_final_price = self.postcard_price
            print(f"DEBUG forms.py save: Установлена postcard_final_price = {self.postcard_price}")
        else:
            # Fallback: если почему-то нет postcard_price
            order.postcard_final_price = Decimal('0.00')

        if commit:
            order.save()
            self.save_m2m()
            print(f"DEBUG forms.py save: Заказ сохранен, ID={order.id}")
            print(f"DEBUG forms.py save: postcard_final_price = {order.postcard_final_price}")
            print(f"DEBUG forms.py save: postcard = {order.postcard}")
            print(f"DEBUG forms.py save: custom_postcard_image = {bool(order.custom_postcard_image)}")

        return order