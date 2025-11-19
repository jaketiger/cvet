# shop/forms.py

from django import forms
from .models import SiteSettings, Banner
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt


class ClearableColorInput(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs, {'type': 'color', 'name': name})
        if value:
            final_attrs['value'] = value

        html = f"""
            <div style="display: flex; align-items: center; gap: 10px; max-width: 200px;">
                <input{flatatt(final_attrs)}>
                <a href="#" class="clear-color-btn" title="Сбросить" style="text-decoration: none; font-size: 1.5em; color: #999;" onclick="this.previousElementSibling.value=''; return false;">&times;</a>
            </div>
        """
        return mark_safe(html)


class RangeSliderWithLabels(forms.NumberInput):
    input_type = 'range'

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name})
        if 'id' not in final_attrs:
            final_attrs['id'] = f'id_{name}'

        if value is not None:
            final_attrs['value'] = str(value)
        else:
            value = '0'

        output_id = f'output_{final_attrs["id"]}'

        html = f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="color: #666; font-size: 0.9em; width: 30px;">0%</span>
                <input{flatatt(final_attrs)} style="flex-grow: 1;" oninput="document.getElementById('{output_id}').textContent = this.value + '%'">
                <span style="color: #666; font-size: 0.9em; width: 40px;">100%</span>
                <span id="{output_id}" style="font-weight: bold; min-width: 45px; text-align: right;">{value}%</span>
            </div>
        """
        return mark_safe(html)


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = '__all__'

        widgets = {
            'default_text_color': ClearableColorInput(),
            'logo_color': ClearableColorInput(),
            'icon_color': ClearableColorInput(),
            'catalog_title_color': ClearableColorInput(),
            'popular_title_color': ClearableColorInput(),
            'category_text_color': ClearableColorInput(),
            'footer_text_color': ClearableColorInput(),
            'product_title_text_color': ClearableColorInput(),
            'product_header_text_color': ClearableColorInput(),
            'accent_color': ClearableColorInput(),
            'button_bg_color': ClearableColorInput(),
            'button_text_color': ClearableColorInput(),
            'button_hover_bg_color': ClearableColorInput(),
            'add_to_cart_bg_color': ClearableColorInput(),
            'add_to_cart_text_color': ClearableColorInput(),
            'add_to_cart_hover_bg_color': ClearableColorInput(),
            'mobile_dropdown_bg_color': ClearableColorInput(),
            'mobile_dropdown_font_color': ClearableColorInput(),
            'mobile_dropdown_button_bg_color': ClearableColorInput(),
            'mobile_dropdown_button_text_color': ClearableColorInput(),

            'mobile_dropdown_opacity': RangeSliderWithLabels(attrs={'min': '0', 'max': '100', 'step': '1'}),
            'mobile_dropdown_button_opacity': RangeSliderWithLabels(attrs={'min': '0', 'max': '100', 'step': '1'}),
            'background_opacity': RangeSliderWithLabels(attrs={'min': '0', 'max': '100', 'step': '1'}),

            'logo_font_size': forms.NumberInput(attrs={'placeholder': '24'}),
            'icon_size': forms.NumberInput(attrs={'placeholder': '22'}),
            'category_font_size': forms.NumberInput(attrs={'placeholder': '16'}),
            'footer_font_size': forms.NumberInput(attrs={'placeholder': '14'}),
            'product_title_font_size': forms.NumberInput(attrs={'placeholder': '18'}),
            'product_header_font_size': forms.NumberInput(attrs={'placeholder': '20'}),
            'button_border_radius': forms.NumberInput(attrs={'placeholder': '5'}),
            'mobile_dropdown_font_size': forms.NumberInput(attrs={'placeholder': '16'}),
            'mobile_dropdown_button_border_radius': forms.NumberInput(attrs={'placeholder': '5'}),
        }


class BannerAdminForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = '__all__'
        widgets = {
            'font_color': ClearableColorInput(),
            'background_opacity': RangeSliderWithLabels(attrs={'min': '0', 'max': '100', 'step': '1'}),
        }