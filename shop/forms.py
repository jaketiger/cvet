# shop/forms.py

from django import forms
from .models import SiteSettings, Banner
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt


class ClearableColorInput(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['type'] = 'color'
        final_attrs['name'] = name
        if value:
            final_attrs['value'] = value

        html = f"""
            <div style="display: flex; align-items: center; gap: 10px; max-width: 200px;">
                <input{flatatt(final_attrs)}>
                <a href="#" class="clear-color-btn" title="Сбросить" style="text-decoration: none; font-size: 1.5em; color: #999;" onclick="this.previousElementSibling.value=''; return false;">&times;</a>
            </div>
        """
        return mark_safe(html)


# --- ВИДЖЕТ ДЛЯ ПРОЗРАЧНОСТИ (0 ... 100) ---
class OpacityRangeSlider(forms.NumberInput):
    input_type = 'range'

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['type'] = self.input_type
        final_attrs['name'] = name
        final_attrs['min'] = '0'
        final_attrs['max'] = '100'
        final_attrs['step'] = '1'

        if value is None or value == '':
            value = '100'
        else:
            try:
                final_attrs['value'] = str(int(float(value)))
            except:
                final_attrs['value'] = str(value)

        output_id = f'output_{final_attrs.get("id", name)}'
        oninput_js = f"document.getElementById('{output_id}').textContent = this.value + '%'"

        # СТРУКТУРА: [Цифра] [Шкала сверху] [Ползунок]
        html = f"""
            <div style="display: flex; align-items: center; gap: 15px; width: 100%;">
                <!-- Текущее значение (СЛЕВА) -->
                <span id="{output_id}" style="font-weight: bold; font-size: 14px; min-width: 40px; text-align: right; color: #333;">{final_attrs['value']}%</span>

                <!-- Блок с ползунком -->
                <div style="flex-grow: 1; display: flex; flex-direction: column;">
                    <!-- Шкала СВЕРХУ -->
                    <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888; margin-bottom: 2px;">
                        <span>0%</span>
                        <span>100%</span>
                    </div>
                    <input{flatatt(final_attrs)} style="width: 100%; cursor: pointer; margin: 0;" oninput="{oninput_js}">
                </div>
            </div>
        """
        return mark_safe(html)


# --- ВИДЖЕТ ДЛЯ КОРРЕКЦИИ ШРИФТА (-50 ... 0 ... +50) ---
class FontScaleRangeSlider(forms.NumberInput):
    input_type = 'range'

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['type'] = self.input_type
        final_attrs['name'] = name
        final_attrs['min'] = '-50'
        final_attrs['max'] = '50'
        # ИЗМЕНЕНО: Шаг 2
        final_attrs['step'] = '2'

        if value is None or value == '':
            final_attrs['value'] = '0'
        else:
            try:
                int_val = int(float(value))
                final_attrs['value'] = str(int_val)
            except:
                final_attrs['value'] = '0'

        output_id = f'output_{final_attrs.get("id", name)}'
        oninput_js = f"let v = parseInt(this.value); let s = v > 0 ? '+' + v : v; document.getElementById('{output_id}').textContent = s + '%'"

        display_val = final_attrs['value']
        try:
            if int(display_val) > 0:
                display_val = f"+{display_val}"
        except:
            pass

        html = f"""
            <div style="display: flex; align-items: center; gap: 15px; width: 100%;">
                <!-- Текущее значение (СЛЕВА) -->
                <span id="{output_id}" style="font-weight: bold; font-size: 14px; min-width: 45px; text-align: right; color: #333;">{display_val}%</span>

                <!-- Блок с ползунком -->
                <div style="flex-grow: 1; display: flex; flex-direction: column;">
                    <!-- Шкала СВЕРХУ -->
                    <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888; margin-bottom: 2px;">
                        <span style="width: 30px; text-align: left;">-50%</span>
                        <span style="width: 30px; text-align: center;">0%</span>
                        <span style="width: 30px; text-align: right;">+50%</span>
                    </div>
                    <input{flatatt(final_attrs)} style="width: 100%; cursor: pointer; margin: 0;" oninput="{oninput_js}">
                </div>
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

            # Используем ОБЫЧНЫЙ слайдер для прозрачности
            'mobile_dropdown_opacity': OpacityRangeSlider(),
            'mobile_dropdown_button_opacity': OpacityRangeSlider(),
            'background_opacity': OpacityRangeSlider(),

            # Используем ЦЕНТРИРОВАННЫЙ слайдер для шрифта
            'mobile_font_scale': FontScaleRangeSlider(),

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
            'background_opacity': OpacityRangeSlider(),
        }