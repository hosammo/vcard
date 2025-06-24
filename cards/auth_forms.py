from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import BusinessCard, ProfileType, PhoneNumber, CountryCode
from django.forms import inlineformset_factory

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


class BusinessCardForm(forms.ModelForm):
    class Meta:
        model = BusinessCard
        fields = [
            'profile_type', 'custom_url', 'first_name', 'last_name',
            'job_title', 'company', 'email', 'phone', 'website', 'address',
            'bio', 'skills', 'profile_photo', 'company_logo', 'banner_image',
            'banner_text', 'background_color', 'accent_color', 'text_color',
            'linkedin_url', 'twitter_url', 'instagram_url', 'facebook_url',
            'portfolio_url', 'custom_link_1_title', 'custom_link_1_url',
            'custom_link_2_title', 'custom_link_2_url'
        ]

        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
            'skills': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'banner_text': forms.TextInput(attrs={'placeholder': 'Optional text for banner'}),
            'background_color': forms.TextInput(attrs={'type': 'color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color'}),
            'text_color': forms.TextInput(attrs={'type': 'color'}),
            'profile_photo': forms.FileInput(attrs={'accept': 'image/*'}),
            'company_logo': forms.FileInput(attrs={'accept': 'image/*'}),
            'banner_image': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name in ['background_color', 'accent_color', 'text_color']:
                field.widget.attrs['class'] = 'form-control color-picker'
            elif field_name in ['profile_photo', 'company_logo', 'banner_image']:
                field.widget.attrs['class'] = 'form-control file-input'
            else:
                field.widget.attrs['class'] = 'form-control'

        # Set help text
        self.fields['custom_url'].help_text = 'Leave blank for auto-generation'
        self.fields[
            'phone'].help_text = 'Include country code (e.g., +965 12345678) - or use phone numbers section below'

    def clean_custom_url(self):
        """Validate custom URL"""
        custom_url = self.cleaned_data.get('custom_url')
        if custom_url:
            # Check if URL already exists
            existing = BusinessCard.objects.filter(custom_url=custom_url)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)

            if existing.exists():
                raise forms.ValidationError('This URL is already taken. Please choose a different one.')

        return custom_url

class PhoneNumberForm(forms.ModelForm):
    class Meta:
        model = PhoneNumber
        fields = ['label', 'country_code', 'number', 'is_primary', 'is_whatsapp']
        widgets = {
            'number': forms.TextInput(attrs={'placeholder': '12345678'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add CSS classes
        for field_name, field in self.fields.items():
            if field_name in ['is_primary', 'is_whatsapp']:
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

        # Set labels
        self.fields['label'].label = 'Type'
        self.fields['country_code'].label = 'Country'
        self.fields['number'].label = 'Number'
        self.fields['is_primary'].label = 'Primary'
        self.fields['is_whatsapp'].label = 'WhatsApp'


try:
    PhoneNumberFormSet = inlineformset_factory(
        BusinessCard,
        PhoneNumber,
        form=PhoneNumberForm,
        extra=1,
        can_delete=True,
        min_num=0,
        validate_min=False
    )
except Exception as e:
    print(f"Error creating PhoneNumberFormSet: {e}")


    # Fallback empty formset
    class EmptyFormSet:
        def __init__(self, *args, **kwargs):
            pass

        def is_valid(self):
            return True

        def save(self):
            pass


    PhoneNumberFormSet = EmptyFormSet

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