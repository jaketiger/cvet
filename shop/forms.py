# shop/forms.py

from django import forms
from .models import SiteSettings, Banner


class ColorInput(forms.TextInput):
    input_type = 'color'


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = '__all__'
        widgets = {
            'main_text_color': ColorInput(),
            'accent_color': ColorInput(),
            'logo_color': ColorInput(),
            'category_nav_font_color': ColorInput(),
            'category_nav_hover_color': ColorInput(),
            'product_card_title_color': ColorInput(),
            'product_card_price_color': ColorInput(),
            'footer_font_color': ColorInput(),
            'button_bg_color': ColorInput(),
            'button_text_color': ColorInput(),
            'button_hover_bg_color': ColorInput(),

            # --- ДОБАВЛЕНО: виджеты для новых полей ---
            'add_to_cart_bg_color': ColorInput(),
            'add_to_cart_text_color': ColorInput(),
            'add_to_cart_hover_bg_color': ColorInput(),
        }


class BannerAdminForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = '__all__'
        widgets = {
            'font_color': ColorInput(),
        }