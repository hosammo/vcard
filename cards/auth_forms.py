from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class CustomUserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes to make forms look better
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150, label='Username')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FIXED: Handle the label properly
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })


from .models import BusinessCard, ProfileType


class BusinessCardForm(forms.ModelForm):
    class Meta:
        model = BusinessCard
        fields = [
            # Basic Info
            'profile_type', 'custom_url', 'first_name', 'last_name',
            'job_title', 'company',

            # Contact Information
            'email', 'phone', 'website', 'address',

            # About
            'bio', 'skills',

            # Images
            'profile_photo', 'company_logo', 'banner_image', 'banner_text',

            # UI Customization
            'background_color', 'accent_color', 'text_color',

            # Social Media
            'linkedin_url', 'twitter_url', 'instagram_url', 'facebook_url',

            # Custom Links
            'portfolio_url', 'custom_link_1_title', 'custom_link_1_url',
            'custom_link_2_title', 'custom_link_2_url'
        ]

        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4,
                                         'placeholder': 'Tell people about yourself, your expertise, and what makes you unique...'}),
            'skills': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'List your skills, services, or areas of expertise...'}),
            'address': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Your business address or location...'}),
            'banner_text': forms.TextInput(attrs={'placeholder': 'Optional text to display on your banner'}),
            'background_color': forms.TextInput(attrs={'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color'}),
            'text_color': forms.TextInput(attrs={'type': 'color'}),
            'profile_photo': forms.FileInput(attrs={'accept': 'image/*'}),
            'company_logo': forms.FileInput(attrs={'accept': 'image/*'}),
            'banner_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add CSS classes to all fields
        for field_name, field in self.fields.items():
            if field_name in ['background_color', 'accent_color', 'text_color']:
                field.widget.attrs['class'] = 'form-control color-picker'
            elif field_name in ['profile_photo', 'company_logo', 'banner_image']:
                field.widget.attrs['class'] = 'form-control file-input'
            else:
                field.widget.attrs['class'] = 'form-control'

        # Custom field labels and help text
        self.fields[
            'custom_url'].help_text = 'Leave blank for auto-generation. Only letters, numbers, and hyphens allowed.'
        self.fields['profile_photo'].help_text = 'Upload your profile picture (recommended: square image, max 2MB)'
        self.fields['company_logo'].help_text = 'Upload your company logo (recommended: rectangular, max 2MB)'
        self.fields[
            'banner_image'].help_text = 'Upload a banner image for the top of your card (recommended: 800x200px, max 2MB)'
        self.fields['background_color'].help_text = 'Primary gradient color'
        self.fields['accent_color'].help_text = 'Secondary gradient color'
        self.fields['text_color'].help_text = 'Text color for the hero section'

        # Set placeholders
        placeholders = {
            'custom_url': 'my-custom-url (optional)',
            'first_name': 'Your first name',
            'last_name': 'Your last name',
            'job_title': 'e.g., Marketing Manager, CEO, Freelance Designer',
            'company': 'Your company or organization name',
            'email': 'your.email@example.com',
            'phone': '+965 12345678',
            'website': 'https://yourwebsite.com',
            'linkedin_url': 'https://linkedin.com/in/yourprofile',
            'twitter_url': 'https://twitter.com/yourusername',
            'instagram_url': 'https://instagram.com/yourusername',
            'facebook_url': 'https://facebook.com/yourpage',
            'portfolio_url': 'https://yourportfolio.com',
            'custom_link_1_title': 'e.g., Blog, YouTube, GitHub',
            'custom_link_1_url': 'https://your-custom-link.com',
            'custom_link_2_title': 'e.g., Calendar, Store, App',
            'custom_link_2_url': 'https://another-link.com',
        }

        for field_name, placeholder in placeholders.items():
            if field_name in self.fields:
                self.fields[field_name].widget.attrs['placeholder'] = placeholder

    def clean_custom_url(self):
        """Validate custom URL"""
        custom_url = self.cleaned_data.get('custom_url')
        if custom_url:
            # Check if URL already exists (excluding current instance)
            existing = BusinessCard.objects.filter(custom_url=custom_url)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError('This URL is already taken. Please choose a different one.')

        return custom_url


# STEP 5: Add these to your cards/auth_forms.py

from .models import BusinessCard, ProfileType, PhoneNumber, CountryCode
from django.forms import inlineformset_factory


class PhoneNumberForm(forms.ModelForm):
    class Meta:
        model = PhoneNumber
        fields = ['label', 'country_code', 'number', 'is_primary', 'is_whatsapp']
        widgets = {
            'country_code': forms.Select(),
            'number': forms.TextInput(attrs={'placeholder': '12345678'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name == 'is_primary' or field_name == 'is_whatsapp':
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

        # Set labels
        self.fields['label'].label = 'Type'
        self.fields['country_code'].label = 'Country'
        self.fields['number'].label = 'Number'
        self.fields['is_primary'].label = 'Primary'
        self.fields['is_whatsapp'].label = 'WhatsApp'


# Create the formset for managing multiple phone numbers
PhoneNumberFormSet = inlineformset_factory(
    BusinessCard,
    PhoneNumber,
    form=PhoneNumberForm,
    extra=1,  # Show 1 empty form by default
    can_delete=True,
    min_num=0,
    validate_min=False
)