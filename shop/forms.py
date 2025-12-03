# shop/forms.py
from django.contrib.admin.widgets import AdminTimeWidget
from django import forms
from .models import SiteSettings, Banner, Product
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt
import uuid
import re


# === ВИДЖЕТЫ ===

class ColorPickerWidget(forms.TextInput):
    def __init__(self, attrs=None):
        default_attrs = {'type': 'color', 'style': 'width: 60px; height: 40px; padding: 0; cursor: pointer;'}
        if attrs: default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)


class ClearableColorInput(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['type'] = 'color'
        final_attrs['name'] = name
        unique_id = final_attrs.get('id', str(uuid.uuid4())[:8])
        picker_id = f"picker_{unique_id}"
        text_id = final_attrs.get('id', f"text_{unique_id}")
        val_for_text = value if value else ''
        val_for_picker = value if value else '#000000'

        js = f"""
        <script>
            (function() {{
                var textInput = document.getElementById('{text_id}');
                var colorInput = document.getElementById('{picker_id}');
                if(textInput && colorInput) {{
                    colorInput.addEventListener('input', function() {{ textInput.value = this.value; }});
                    textInput.addEventListener('input', function() {{ if(this.value.match(/^#[0-9A-F]{{6}}$/i)) {{ colorInput.value = this.value; }} }});
                }}
            }})();
        </script>
        """
        html = f"""
            <div style="display: flex; align-items: center; gap: 5px;">
                <input type="text" name="{name}" id="{text_id}" value="{val_for_text}" placeholder="По умолч." style="width: 80px; padding: 5px; border: 1px solid #ccc; border-radius: 3px;">
                <input type="color" id="{picker_id}" value="{val_for_picker}" style="height: 30px; width: 30px; padding: 0; border: none; background: none; cursor: pointer;">
                <a href="#" title="Сбросить" style="text-decoration: none; font-size: 18px; color: #d9534f; font-weight: bold; line-height: 1;" onclick="document.getElementById('{text_id}').value=''; return false;">&times;</a>
            </div>
            {js}
        """
        return mark_safe(html)


class HybridRangeWidget(forms.NumberInput):
    """
    Виджет: Числовое поле + Ползунок.
    Синхронизированы через JS.
    """

    def __init__(self, min_val=0, max_val=100, step=1, attrs=None):
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        value = value if value is not None else self.min_val
        input_id = final_attrs.get('id', name)
        range_id = f"range_{input_id}"

        style_wrapper = "display: flex; align-items: center; gap: 15px; width: 100%; max-width: 400px;"
        style_input = "width: 80px; text-align: center; font-weight: bold; padding: 5px;"
        style_range = "flex-grow: 1; cursor: pointer;"

        html = f"""
        <div style="{style_wrapper}">
            <input type="number" name="{name}" value="{value}" id="{input_id}" 
                   min="{self.min_val}" max="{self.max_val}" step="{self.step}"
                   style="{style_input}" 
                   oninput="document.getElementById('{range_id}').value = this.value">

            <input type="range" value="{value}" id="{range_id}" 
                   min="{self.min_val}" max="{self.max_val}" step="{self.step}"
                   style="{style_range}"
                   oninput="document.getElementById('{input_id}').value = this.value">

            <span style="font-size: 12px; color: #888;">{self.max_val}px</span>
        </div>
        """
        return mark_safe(html)


class OpacityRangeSlider(forms.NumberInput):
    input_type = 'range'

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['type'] = self.input_type
        final_attrs['name'] = name
        final_attrs['min'] = '0'
        final_attrs['max'] = '100'
        final_attrs['step'] = '1'
        if value is None: value = final_attrs.get('value', '100')
        if value == '': value = '100'
        try:
            final_value = str(int(float(str(value))))
        except:
            final_value = '100'
        final_attrs['value'] = final_value
        output_id = f'output_{final_attrs.get("id", name)}'
        oninput_js = f"document.getElementById('{output_id}').textContent = this.value + '%'"
        html = f"""<div style="display: flex; align-items: center; gap: 15px; width: 100%;"><span id="{output_id}" style="font-weight: bold; font-size: 14px; min-width: 40px; text-align: right; color: #333;">{final_value}%</span><div style="flex-grow: 1; display: flex; flex-direction: column;"><div style="display: flex; justify-content: space-between; font-size: 10px; color: #888; margin-bottom: 2px;"><span>0%</span><span>100%</span></div><input{flatatt(final_attrs)} style="width: 100%; cursor: pointer; margin: 0;" oninput="{oninput_js}"></div></div>"""
        return mark_safe(html)


class BlurRangeSlider(forms.NumberInput):
    input_type = 'range'

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['type'] = self.input_type
        final_attrs['name'] = name
        final_attrs['min'] = '0'
        final_attrs['max'] = '20'
        final_attrs['step'] = '1'
        if value is None: value = final_attrs.get('value', '0')
        if value == '': value = '0'
        try:
            final_value = str(int(float(str(value))))
        except:
            final_value = '0'
        final_attrs['value'] = final_value
        output_id = f'output_{final_attrs.get("id", name)}'
        oninput_js = f"document.getElementById('{output_id}').textContent = this.value + 'px'"
        html = f"""<div style="display: flex; align-items: center; gap: 15px; width: 100%;"><span id="{output_id}" style="font-weight: bold; font-size: 14px; min-width: 40px; text-align: right; color: #333;">{final_value}px</span><div style="flex-grow: 1; display: flex; flex-direction: column;"><div style="display: flex; justify-content: space-between; font-size: 10px; color: #888; margin-bottom: 2px;"><span>0px</span><span>20px</span></div><input{flatatt(final_attrs)} style="width: 100%; cursor: pointer; margin: 0;" oninput="{oninput_js}"></div></div>"""
        return mark_safe(html)


class FontScaleRangeSlider(forms.NumberInput):
    input_type = 'range'

    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['type'] = self.input_type
        final_attrs['name'] = name
        final_attrs['min'] = '-50'
        final_attrs['max'] = '50'
        final_attrs['step'] = '2'
        if value is None: value = final_attrs.get('value', '0')
        if value == '': value = '0'
        try:
            final_value = str(int(float(str(value))))
        except:
            final_value = '0'
        final_attrs['value'] = final_value
        output_id = f'output_{final_attrs.get("id", name)}'
        oninput_js = f"let v = parseInt(this.value); let s = v > 0 ? '+' + v : v; document.getElementById('{output_id}').textContent = s + '%'"
        display_val = final_value
        try:
            if int(display_val) > 0: display_val = f"+{display_val}"
        except:
            pass
        html = f"""<div style="display: flex; align-items: center; gap: 15px; width: 100%;"><span id="{output_id}" style="font-weight: bold; font-size: 14px; min-width: 45px; text-align: right; color: #333;">{display_val}%</span><div style="flex-grow: 1; display: flex; flex-direction: column;"><div style="display: flex; justify-content: space-between; font-size: 10px; color: #888; margin-bottom: 2px;"><span style="width: 30px; text-align: left;">-50%</span><span style="width: 30px; text-align: center;">0%</span><span style="width: 30px; text-align: right;">+50%</span></div><input{flatatt(final_attrs)} style="width: 100%; cursor: pointer; margin: 0;" oninput="{oninput_js}"></div></div>"""
        return mark_safe(html)


# === ФОРМЫ ===

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = '__all__'
        widgets = {
            # === ДОБАВЛЯЕМ ЭТОТ БЛОК ДЛЯ ВРЕМЕНИ ===
            'work_weekdays_open': AdminTimeWidget(),
            'work_weekdays_close': AdminTimeWidget(),
            'work_weekend_open': AdminTimeWidget(),
            'work_weekend_close': AdminTimeWidget(),
            'delivery_weekdays_open': AdminTimeWidget(),
            'delivery_weekdays_close': AdminTimeWidget(),
            'delivery_weekend_open': AdminTimeWidget(),
            'delivery_weekend_close': AdminTimeWidget(),
            # =======================================
            'discount_colors_mode': forms.Select(attrs={'style': 'width: 300px;'}),
            'default_discount_sticker_color': ClearableColorInput(),
            'default_new_price_color': ClearableColorInput(),
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
            'button_accent_color': ClearableColorInput(),
            'button_text_color': ClearableColorInput(),
            'button_hover_bg_color': ClearableColorInput(),
            'add_to_cart_bg_color': ClearableColorInput(),
            'add_to_cart_text_color': ClearableColorInput(),
            'add_to_cart_hover_bg_color': ClearableColorInput(),
            'mobile_dropdown_bg_color': ClearableColorInput(),
            'mobile_dropdown_font_color': ClearableColorInput(),
            'mobile_dropdown_button_bg_color': ClearableColorInput(),
            'mobile_dropdown_button_text_color': ClearableColorInput(),
            'desktop_categories_bg_color': ClearableColorInput(),
            'mobile_header_bg_color_custom': ClearableColorInput(),
            'site_sheet_bg_color': ClearableColorInput(),
            'static_page_title_color': ClearableColorInput(),
            'static_page_subtitle_color': ClearableColorInput(),
            'static_page_icon_color': ClearableColorInput(),
            'static_page_link_color': ClearableColorInput(),
            'static_page_link_hover_color': ClearableColorInput(),

            'mobile_dropdown_opacity': OpacityRangeSlider(),
            'mobile_dropdown_button_opacity': OpacityRangeSlider(),
            'background_opacity': OpacityRangeSlider(),
            'desktop_header_scroll_opacity': OpacityRangeSlider(),
            'mobile_header_scroll_opacity': OpacityRangeSlider(),
            'desktop_categories_opacity': OpacityRangeSlider(),
            'site_sheet_opacity': OpacityRangeSlider(),
            'site_sheet_blur': BlurRangeSlider(),
            'desktop_header_blur': BlurRangeSlider(),
            'desktop_category_blur': BlurRangeSlider(),
            'mobile_header_blur': BlurRangeSlider(),
            'mobile_font_scale': FontScaleRangeSlider(),

            'logo_font_size': forms.NumberInput(attrs={'placeholder': '24'}),
            'icon_size': forms.NumberInput(attrs={'placeholder': '22'}),
            'category_font_size': forms.NumberInput(attrs={'placeholder': '16'}),
            'footer_font_size': forms.NumberInput(attrs={'placeholder': '14'}),
            'product_title_font_size': forms.NumberInput(attrs={'placeholder': '18'}),
            'product_header_font_size': forms.NumberInput(attrs={'placeholder': '20'}),
            'heading_font_size': forms.NumberInput(attrs={'placeholder': '24'}),
            'button_border_radius': forms.NumberInput(attrs={'placeholder': '5'}),
            'mobile_dropdown_font_size': forms.NumberInput(attrs={'placeholder': '16'}),
            'mobile_dropdown_button_border_radius': forms.NumberInput(attrs={'placeholder': '5'}),
        }

    def clean_default_discount_sticker_color(self):
        color = self.cleaned_data.get('default_discount_sticker_color', '')
        if color and not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color):
            raise forms.ValidationError("Введите корректный HEX-цвет")
        return color

    def clean_default_new_price_color(self):
        color = self.cleaned_data.get('default_new_price_color', '')
        if color and not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color):
            raise forms.ValidationError("Введите корректный HEX-цвет")
        return color


class BannerAdminForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = '__all__'
        widgets = {
            'font_color': ClearableColorInput(),
            'background_opacity': OpacityRangeSlider(),
        }


class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'discount_sticker_color': ClearableColorInput(),
            'new_price_color': ClearableColorInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[
            'discount_sticker_color'].help_text = "Нажмите крестик (×), чтобы сбросить. Тогда применится цвет из Глобальных настроек."
        self.fields[
            'new_price_color'].help_text = "Нажмите крестик (×), чтобы сбросить. Тогда применится цвет из Глобальных настроек."

    def clean_discount_sticker_color(self):
        color = self.cleaned_data.get('discount_sticker_color', '')
        if color and not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color):
            raise forms.ValidationError("Введите корректный HEX-цвет")
        return color

    def clean_new_price_color(self):
        color = self.cleaned_data.get('new_price_color', '')
        if color and not re.match(r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$', color):
            raise forms.ValidationError("Введите корректный HEX-цвет")
        return color


# === НОВАЯ ФОРМА ДЛЯ ПАНЕЛИ НАСТРОЕК СЛАЙДЕРА ===
class SliderSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'slider_duration', 'slider_effect',
            'slider_height_desktop', 'slider_desktop_fit_mode',
            'slider_height_mobile', 'slider_mobile_fit_mode'
        ]
        widgets = {
            # Используем гибридные ползунки
            'slider_height_desktop': HybridRangeWidget(min_val=300, max_val=1200, step=20),
            'slider_height_mobile': HybridRangeWidget(min_val=100, max_val=700, step=20),
            # Радио кнопки для режимов
            'slider_desktop_fit_mode': forms.RadioSelect(attrs={'class': 'radio-inline'}),
            'slider_mobile_fit_mode': forms.RadioSelect(attrs={'class': 'radio-inline'}),
        }

class PostcardSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = ['custom_postcard_price']


