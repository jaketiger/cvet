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
                <a href="#" class="clear-color-btn" title="Сбросить к значению по умолчанию" style="text-decoration: none; font-size: 1.5em; color: #999;" onclick="this.previousElementSibling.value=''; return false;">&times;</a>
            </div>
        """
        return mark_safe(html)


class RangeSliderWithLabels(forms.NumberInput):
    input_type = 'range'

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(attrs, {'type': self.input_type, 'name': name})
        if value is not None:
            final_attrs['value'] = str(value)

        html = f"""
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="color: #999; font-size: 0.9em;">0%</span>
                <input{flatatt(final_attrs)} style="flex-grow: 1;">
                <span style="color: #999; font-size: 0.9em;">100%</span>
            </div>
        """
        return mark_safe(html)


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        # ===== НАЧАЛО ИЗМЕНЕНИЙ: Заменяем '__all__' на явный список полей =====
        fields = (
            # Основные настройки
            'shop_name', 'contact_phone', 'admin_notification_emails',
            'delivery_cost', 'background_image',
            # Настройки каталога и товара
            'all_products_text', 'default_composition_title', 'default_description_title',
            # Настройки слайдера
            'slider_duration', 'slider_effect',
            # Глобальное оформление
            'navigation_style', 'icon_animation_style',
            'default_font_family', 'default_font_size', 'default_text_color',
            'logo_font_family', 'logo_font_size', 'logo_color',
            'icon_size', 'icon_color',
            'category_font_family', 'category_font_size', 'category_text_color',
            'footer_font_family', 'footer_font_size', 'footer_text_color',
            'product_title_font_family', 'product_title_font_size', 'product_title_text_color',
            'product_header_font_family', 'product_header_font_size', 'product_header_text_color',
            'heading_font_family', 'accent_color',
            # Настройки кнопок
            'button_bg_color', 'button_text_color', 'button_hover_bg_color',
            'add_to_cart_bg_color', 'add_to_cart_text_color', 'add_to_cart_hover_bg_color',
            'button_border_radius', 'button_font_family',
            # Настройки мобильной версии
            'mobile_view_mode', 'mobile_header_style', 'mobile_product_grid',
            'collapse_categories_threshold', 'collapse_footer_threshold',
            'mobile_dropdown_bg_color', 'mobile_dropdown_opacity',
            'mobile_dropdown_font_family', 'mobile_dropdown_font_size',
            'mobile_dropdown_font_color', 'mobile_dropdown_button_bg_color',
            'mobile_dropdown_button_text_color', 'mobile_dropdown_button_border_radius',
            'mobile_dropdown_button_opacity'
        )
        # ===== КОНЕЦ ИЗМЕНЕНИЙ =====

        widgets = {
            'default_text_color': ClearableColorInput(),
            'logo_color': ClearableColorInput(),
            'icon_color': ClearableColorInput(),
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