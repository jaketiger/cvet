# shop/forms.py

from django import forms
from .models import SiteSettings, Banner
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt
import uuid


class ClearableColorInput(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        final_attrs = self.build_attrs(self.attrs, attrs)
        final_attrs['type'] = 'color'
        final_attrs['name'] = name

        unique_id = final_attrs.get('id', str(uuid.uuid4())[:8])
        picker_id = f"picker_{unique_id}"
        text_id = final_attrs.get('id', f"text_{unique_id}")

        val = value if value else ''

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
                <input type="text" name="{name}" id="{text_id}" value="{val}" placeholder="#RRGGBB" style="width: 80px; padding: 5px; border: 1px solid #ccc; border-radius: 3px;">
                <input type="color" id="{picker_id}" value="{val if val else '#ffffff'}" style="height: 30px; width: 30px; padding: 0; border: none; background: none; cursor: pointer;">
                <a href="#" title="Очистить" style="text-decoration: none; font-size: 18px; color: #d9534f; font-weight: bold; line-height: 1;" onclick="document.getElementById('{text_id}').value=''; return false;">&times;</a>
            </div>
            {js}
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
        except (ValueError, TypeError):
            final_value = '100'
        final_attrs['value'] = final_value

        output_id = f'output_{final_attrs.get("id", name)}'
        oninput_js = f"document.getElementById('{output_id}').textContent = this.value + '%'"

        html = f"""
            <div style="display: flex; align-items: center; gap: 15px; width: 100%;">
                <span id="{output_id}" style="font-weight: bold; font-size: 14px; min-width: 40px; text-align: right; color: #333;">{final_value}%</span>
                <div style="flex-grow: 1; display: flex; flex-direction: column;">
                    <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888; margin-bottom: 2px;"><span>0%</span><span>100%</span></div>
                    <input{flatatt(final_attrs)} style="width: 100%; cursor: pointer; margin: 0;" oninput="{oninput_js}">
                </div>
            </div>
        """
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
        except (ValueError, TypeError):
            final_value = '0'
        final_attrs['value'] = final_value

        output_id = f'output_{final_attrs.get("id", name)}'
        oninput_js = f"document.getElementById('{output_id}').textContent = this.value + 'px'"

        html = f"""
            <div style="display: flex; align-items: center; gap: 15px; width: 100%;">
                <span id="{output_id}" style="font-weight: bold; font-size: 14px; min-width: 40px; text-align: right; color: #333;">{final_value}px</span>
                <div style="flex-grow: 1; display: flex; flex-direction: column;">
                    <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888; margin-bottom: 2px;"><span>0px</span><span>20px</span></div>
                    <input{flatatt(final_attrs)} style="width: 100%; cursor: pointer; margin: 0;" oninput="{oninput_js}">
                </div>
            </div>
        """
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
        except (ValueError, TypeError):
            final_value = '0'
        final_attrs['value'] = final_value

        output_id = f'output_{final_attrs.get("id", name)}'
        oninput_js = f"let v = parseInt(this.value); let s = v > 0 ? '+' + v : v; document.getElementById('{output_id}').textContent = s + '%'"

        display_val = final_value
        try:
            if int(display_val) > 0: display_val = f"+{display_val}"
        except:
            pass

        html = f"""
            <div style="display: flex; align-items: center; gap: 15px; width: 100%;">
                <span id="{output_id}" style="font-weight: bold; font-size: 14px; min-width: 45px; text-align: right; color: #333;">{display_val}%</span>
                <div style="flex-grow: 1; display: flex; flex-direction: column;">
                    <div style="display: flex; justify-content: space-between; font-size: 10px; color: #888; margin-bottom: 2px;">
                        <span style="width: 30px; text-align: left;">-50%</span><span style="width: 30px; text-align: center;">0%</span><span style="width: 30px; text-align: right;">+50%</span>
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

            # Удалены виджеты для product_image_zoom_factor и product_button_size
            # 'product_image_zoom_factor': ZoomRangeSlider(),
            # 'product_button_size': forms.Select(choices=BUTTON_SIZE_CHOICES), # Этот виджет также удален

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


class BannerAdminForm(forms.ModelForm):
    class Meta:
        model = Banner
        fields = '__all__'
        widgets = {
            'font_color': ClearableColorInput(),
            'background_opacity': OpacityRangeSlider(),
        }