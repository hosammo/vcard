# cards/models.py
import uuid
import qrcode
import os
from io import BytesIO
from django.db import models
from django.core.files import File
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import RegexValidator
from PIL import Image


class ProfileType(models.TextChoices):
    PERSONAL = 'personal', 'Personal'
    BUSINESS = 'business', 'Business'
    FREELANCE = 'freelance', 'Freelance'
    ACADEMIC = 'academic', 'Academic'
    CREATIVE = 'creative', 'Creative'


class CountryCode(models.Model):
    """Country codes with flags for phone numbers"""
    country_name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=10)  # e.g., "+965", "+1"
    flag_emoji = models.CharField(max_length=10)  # e.g., "🇰🇼", "🇺🇸"
    iso_code = models.CharField(max_length=2)  # e.g., "KW", "US"

    class Meta:
        ordering = ['country_name']
        verbose_name = "Country Code"
        verbose_name_plural = "Country Codes"

    def __str__(self):
        return f"{self.flag_emoji} {self.country_name} ({self.country_code})"


class BusinessCard(models.Model):
    # Basic Info
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_type = models.CharField(
        max_length=20,
        choices=ProfileType.choices,
        default=ProfileType.PERSONAL
    )

    # URL Management
    custom_url = models.SlugField(
        max_length=50,
        unique=True,
        blank=True,
        help_text="Custom URL path (leave blank for auto-generation)"
    )

    # Contact Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    job_title = models.CharField(max_length=100, blank=True)
    company = models.CharField(max_length=100, blank=True)

    # Contact Details
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)  # Keep for backward compatibility
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)

    # Bio & Description
    bio = models.TextField(max_length=500, blank=True, help_text="Short bio or description")
    skills = models.TextField(blank=True, help_text="Skills or services offered")

    # Images
    profile_photo = models.ImageField(upload_to='profiles/', blank=True, null=True)
    company_logo = models.ImageField(upload_to='logos/', blank=True, null=True)

    # UI Customization
    background_color = models.CharField(
        max_length=7,
        default='#667eea',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$', 'Enter a valid hex color code')],
        help_text="Background gradient start color (hex format: #667eea)"
    )
    accent_color = models.CharField(
        max_length=7,
        default='#764ba2',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$', 'Enter a valid hex color code')],
        help_text="Background gradient end color (hex format: #764ba2)"
    )
    text_color = models.CharField(
        max_length=7,
        default='#ffffff',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$', 'Enter a valid hex color code')],
        help_text="Text color for hero section (hex format: #ffffff)"
    )

    # Banner Support
    banner_image = models.ImageField(
        upload_to='banners/',
        blank=True,
        null=True,
        help_text="Banner image displayed at the top of the card"
    )
    banner_text = models.CharField(
        max_length=100,
        blank=True,
        help_text="Text overlay on banner (optional)"
    )

    # Social Media
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)

    # Custom Links
    portfolio_url = models.URLField(blank=True)
    custom_link_1_title = models.CharField(max_length=50, blank=True)
    custom_link_1_url = models.URLField(blank=True)
    custom_link_2_title = models.CharField(max_length=50, blank=True)
    custom_link_2_url = models.URLField(blank=True)

    # QR Code
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    # Status & Settings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Business Card"
        verbose_name_plural = "Business Cards"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.profile_type}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_title(self):
        if self.job_title and self.company:
            return f"{self.job_title} at {self.company}"
        elif self.job_title:
            return self.job_title
        elif self.company:
            return self.company
        return ""

    @property
    def primary_phone(self):
        """Get the primary phone number"""
        return self.phone_numbers.filter(is_primary=True).first()

    @property
    def gradient_style(self):
        """Generate CSS gradient style"""
        return f"linear-gradient(135deg, {self.background_color} 0%, {self.accent_color} 100%)"

    def get_absolute_url(self):
        return reverse('card_detail', kwargs={'url_slug': self.custom_url})

    def get_full_url(self):
        """Get full URL for QR code and NFC"""
        return f"https://hosammo.com{self.get_absolute_url()}"

    def get_location_stats(self):
        """Get visitor location statistics"""
        from django.db.models import Count
        return self.views.values('country', 'city').annotate(
            count=Count('id')
        ).order_by('-count')

    def get_daily_views(self, days=30):
        """Get daily view counts for the last N days"""
        from django.utils import timezone
        from django.db.models import Count
        from datetime import timedelta

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        return self.views.filter(
            timestamp__gte=start_date
        ).extra(
            select={'day': 'date(timestamp)'}
        ).values('day').annotate(
            views=Count('id')
        ).order_by('day')

    def save(self, *args, **kwargs):
        # Auto-generate custom_url if not provided
        if not self.custom_url:
            base_slug = slugify(f"{self.first_name}-{self.last_name}")
            unique_slug = base_slug
            counter = 1

            while BusinessCard.objects.filter(custom_url=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1

            self.custom_url = unique_slug

        super().save(*args, **kwargs)

        # Generate QR code after saving (so we have the URL)
        if not self.qr_code:
            self.generate_qr_code()

    def generate_qr_code(self):
        """Generate QR code for the business card URL"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.get_full_url())
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Save to BytesIO
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        # Save to model field
        filename = f"qr_{self.custom_url}.png"
        self.qr_code.save(filename, File(buffer), save=False)
        buffer.close()

        # Save the model (without triggering save() again)
        BusinessCard.objects.filter(pk=self.pk).update(qr_code=self.qr_code)


class PhoneNumber(models.Model):
    """Multiple phone numbers per business card"""
    PHONE_TYPES = [
        ('mobile', 'Mobile'),
        ('work', 'Work'),
        ('home', 'Home'),
        ('fax', 'Fax'),
        ('other', 'Other'),
    ]

    business_card = models.ForeignKey(BusinessCard, on_delete=models.CASCADE, related_name='phone_numbers')
    label = models.CharField(max_length=50, choices=PHONE_TYPES, default='mobile')
    country_code = models.ForeignKey(CountryCode, on_delete=models.CASCADE)
    number = models.CharField(max_length=20, help_text="Phone number without country code")
    is_primary = models.BooleanField(default=False, help_text="Primary contact number")
    is_whatsapp = models.BooleanField(default=False, help_text="Available on WhatsApp")

    class Meta:
        ordering = ['-is_primary', 'label']
        verbose_name = "Phone Number"
        verbose_name_plural = "Phone Numbers"

    def __str__(self):
        return f"{self.country_code.country_code} {self.number} ({self.get_label_display()})"

    @property
    def full_number(self):
        return f"{self.country_code.country_code}{self.number}"

    @property
    def formatted_number(self):
        return f"{self.country_code.flag_emoji} {self.country_code.country_code} {self.number}"

    @property
    def whatsapp_url(self):
        if self.is_whatsapp:
            # Remove + and spaces for WhatsApp URL
            clean_number = self.full_number.replace('+', '').replace(' ', '')
            return f"https://wa.me/{clean_number}"
        return None

    def save(self, *args, **kwargs):
        # Ensure only one primary phone per card
        if self.is_primary:
            PhoneNumber.objects.filter(
                business_card=self.business_card,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class CardView(models.Model):
    """Track views/visits for each business card"""
    card = models.ForeignKey(BusinessCard, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referer = models.URLField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    # Enhanced location data
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Card View"
        verbose_name_plural = "Card Views"

    def __str__(self):
        return f"View of {self.card.full_name} at {self.timestamp}"


class ContactDownload(models.Model):
    """Track when someone downloads/saves contact info"""
    card = models.ForeignKey(BusinessCard, on_delete=models.CASCADE, related_name='downloads')
    ip_address = models.GenericIPAddressField()
    download_type = models.CharField(
        max_length=20,
        choices=[
            ('vcard', 'vCard Download'),
            ('contact', 'Add to Contacts'),
        ],
        default='vcard'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Contact Download"
        verbose_name_plural = "Contact Downloads"

    def __str__(self):
        return f"Download of {self.card.full_name} - {self.download_type}"