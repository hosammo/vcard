# cards/forms.py
from django import forms
from .models import BusinessCard, PhoneNumber, CountryCode
from .widgets import ColorPickerWidget, SearchableCountryWidget


class BusinessCardAdminForm(forms.ModelForm):
    """Custom form for BusinessCard admin with color pickers"""

    class Meta:
        model = BusinessCard
        fields = '__all__'
        widgets = {
            'background_color': ColorPickerWidget(),
            'accent_color': ColorPickerWidget(),
            'text_color': ColorPickerWidget(),
        }


class PhoneNumberAdminForm(forms.ModelForm):
    """Custom form for PhoneNumber with searchable country widget"""

    class Meta:
        model = PhoneNumber
        fields = '__all__'
        widgets = {
            'country_code': SearchableCountryWidget(),
        }