# cards/models.py - COMPLETE FILE
import uuid
import qrcode
import os
import re
from io import BytesIO
from django.db import models
from django.core.files import File
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
from .utils import process_uploaded_image

User = get_user_model()


# ── Plan configuration ────────────────────────────────────────────────────────

class Plan(models.TextChoices):
    FREE     = 'free',     'Free'
    PRO      = 'pro',      'Pro'
    BUSINESS = 'business', 'Business'


PLAN_LIMITS = {
    Plan.FREE:     {'cards': 1,   'seats': 1,  'analytics': False, 'csv_export': False},
    Plan.PRO:      {'cards': 5,   'seats': 1,  'analytics': True,  'csv_export': True},
    Plan.BUSINESS: {'cards': 999, 'seats': 10, 'analytics': True,  'csv_export': True},
}


# ── Organization ──────────────────────────────────────────────────────────────

class Organization(models.Model):
    """A workspace/team that owns business cards and has a subscription plan."""
    id                     = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name                   = models.CharField(max_length=100)
    slug                   = models.SlugField(max_length=60, unique=True)
    plan                   = models.CharField(max_length=20, choices=Plan.choices, default=Plan.FREE)
    stripe_customer_id     = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    is_active              = models.BooleanField(default=True)
    created_at             = models.DateTimeField(auto_now_add=True)
    updated_at             = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'

    def __str__(self):
        return f"{self.name} ({self.plan})"

    # ── Plan limits ──────────────────────────────────────────────────────────

    @property
    def limits(self):
        return PLAN_LIMITS.get(self.plan, PLAN_LIMITS[Plan.FREE])

    @property
    def card_limit(self):
        return self.limits['cards']

    @property
    def seat_limit(self):
        return self.limits['seats']

    @property
    def has_analytics(self):
        return self.limits['analytics']

    @property
    def has_csv_export(self):
        return self.limits['csv_export']

    # ── Capacity checks ──────────────────────────────────────────────────────

    @property
    def card_count(self):
        return self.business_cards.count()

    @property
    def seat_count(self):
        return self.members.filter(invite_accepted=True).count()

    @property
    def can_add_card(self):
        return self.card_count < self.card_limit

    @property
    def can_add_member(self):
        return self.seat_count < self.seat_limit

    # ── Member helpers ───────────────────────────────────────────────────────

    def get_member(self, user):
        """Return OrganizationMember for this user, or None."""
        return self.members.filter(user=user, invite_accepted=True).first()

    def has_member(self, user):
        return self.members.filter(user=user, invite_accepted=True).exists()

    def get_owner(self):
        m = self.members.filter(role=OrganizationMember.Role.OWNER).first()
        return m.user if m else None


# ── Organization Member ───────────────────────────────────────────────────────

class OrganizationMember(models.Model):
    """A user's membership (or pending invite) in an Organization."""

    class Role(models.TextChoices):
        OWNER  = 'owner',  'Owner'
        ADMIN  = 'admin',  'Admin'
        EDITOR = 'editor', 'Editor'
        VIEWER = 'viewer', 'Viewer'

    organization   = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')
    user           = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                       related_name='org_memberships')
    role           = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    invited_email  = models.EmailField(blank=True, help_text='Email used for pending invites')
    invite_token   = models.UUIDField(default=uuid.uuid4, null=True, blank=True)
    invite_accepted = models.BooleanField(default=False)
    joined_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['role', 'joined_at']
        unique_together = [('organization', 'user')]
        verbose_name = 'Organization Member'
        verbose_name_plural = 'Organization Members'

    def __str__(self):
        name = self.user.username if self.user else self.invited_email
        return f"{name} — {self.role} @ {self.organization.name}"

    # ── Permission shortcuts ─────────────────────────────────────────────────

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def can_edit(self):
        """Can create / edit cards."""
        return self.role in (self.Role.OWNER, self.Role.ADMIN, self.Role.EDITOR)

    @property
    def can_manage_members(self):
        """Can invite / remove team members."""
        return self.role in (self.Role.OWNER, self.Role.ADMIN)

    @property
    def can_manage_billing(self):
        """Only the owner manages billing."""
        return self.role == self.Role.OWNER


def validate_hex_color(value):
    """Validate hex color format"""
    if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
        raise ValidationError('Enter a valid hex color code (e.g., #FF0000)')


def validate_phone_number(value):
    """Validate phone number format"""
    if value and not re.match(r'^\+?[\d\s\-\(\)]+$', value):
        raise ValidationError('Enter a valid phone number')


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
    # Organization relationship (primary ownership — Phase 1A)
    organization = models.ForeignKey(
        'Organization',
        on_delete=models.CASCADE,
        related_name='business_cards',
        null=True, blank=True,
        help_text='The organization/workspace this card belongs to',
    )
    # Legacy direct owner — kept for backward-compat until views are migrated (Phase 1B)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='business_cards', null=True, blank=True)

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
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[validate_phone_number],
        help_text="Include country code (e.g., +965 12345678)"
    )
    website = models.URLField(blank=True)
    address = models.TextField(blank=True)

    # Bio & Description
    bio = models.TextField(max_length=500, blank=True, help_text="Short bio or description")
    skills = models.TextField(blank=True, help_text="Skills or services offered")

    # Images
    profile_photo = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        help_text="📸 Profile photo - Supports JPEG, PNG, WebP, AVIF formats. Max size: 5MB. Will be optimized to 400x400px automatically."
    )
    company_logo = models.ImageField(
        upload_to='logos/',
        blank=True,
        null=True,
        help_text="🏢 Company logo - Supports JPEG, PNG, WebP, AVIF formats. Max size: 5MB. Will be optimized to 200x100px automatically."
    )
    # UI Customization
    background_color = models.CharField(
        max_length=7,
        default='#667eea',
        validators=[validate_hex_color],
        help_text="Background gradient start color (hex format: #667eea)"
    )
    accent_color = models.CharField(
        max_length=7,
        default='#764ba2',
        validators=[validate_hex_color],
        help_text="Background gradient end color (hex format: #764ba2)"
    )
    text_color = models.CharField(
        max_length=7,
        default='#ffffff',
        validators=[validate_hex_color],
        help_text="Text color for hero section (hex format: #ffffff)"
    )

    # Banner Support
    banner_image = models.ImageField(
        upload_to='banners/',
        blank=True,
        null=True,
        help_text="🖼️ Banner image - Supports JPEG, PNG, WebP, AVIF formats. Max size: 5MB. Will be optimized to 800x300px automatically."
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

    def save(self, *args, **kwargs):
        # Process images before saving if they're new uploads
        if self.profile_photo and hasattr(self.profile_photo, 'file'):
            self.profile_photo = process_uploaded_image(self.profile_photo, 'profile')

        if self.company_logo and hasattr(self.company_logo, 'file'):
            self.company_logo = process_uploaded_image(self.company_logo, 'logo')

        if self.banner_image and hasattr(self.banner_image, 'file'):
            self.banner_image = process_uploaded_image(self.banner_image, 'banner')

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
        try:
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
        except Exception as e:
            print(f"Error generating QR code: {e}")


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


class CardInteraction(models.Model):
    """Track individual link/button clicks on a business card"""
    INTERACTION_TYPES = [
        ('email_click',      'Email Click'),
        ('phone_click',      'Phone Click'),
        ('whatsapp_click',   'WhatsApp Click'),
        ('website_click',    'Website Click'),
        ('vcard_download',   'vCard Download'),
        ('social_linkedin',  'LinkedIn'),
        ('social_twitter',   'Twitter/X'),
        ('social_instagram', 'Instagram'),
        ('social_facebook',  'Facebook'),
        ('social_portfolio', 'Portfolio'),
        ('custom_link',      'Custom Link'),
    ]
    card             = models.ForeignKey(BusinessCard, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=50, choices=INTERACTION_TYPES)
    ip_address       = models.GenericIPAddressField(null=True, blank=True)
    timestamp        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Card Interaction"
        verbose_name_plural = "Card Interactions"

    def __str__(self):
        return f"{self.interaction_type} on {self.card.full_name} at {self.timestamp}"


class CardLead(models.Model):
    """A visitor-submitted contact enquiry from a public card page."""
    card       = models.ForeignKey(BusinessCard, on_delete=models.CASCADE, related_name='leads')
    name       = models.CharField(max_length=120)
    email      = models.EmailField()
    phone      = models.CharField(max_length=30, blank=True)
    message    = models.TextField(max_length=1000)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_read    = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Card Lead'
        verbose_name_plural = 'Card Leads'

    def __str__(self):
        return f"Lead from {self.name} on {self.card.full_name}"


# ── User Settings ─────────────────────────────────────────────────────────────

class UserSettings(models.Model):
    """Per-user notification and privacy preferences."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')

    # Notifications
    email_notifications            = models.BooleanField(default=True)
    card_view_alerts               = models.BooleanField(default=False)
    contact_download_notifications = models.BooleanField(default=False)
    marketing_emails               = models.BooleanField(default=False)
    weekly_reports                 = models.BooleanField(default=True)
    billing_updates                = models.BooleanField(default=True)

    # Privacy
    public_profile          = models.BooleanField(default=True)
    search_engine_indexing  = models.BooleanField(default=True)
    analytics_tracking      = models.BooleanField(default=True)
    data_sharing            = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'

    def __str__(self):
        return f"Settings for {self.user.username}"


# ── Activity Log ───────────────────────────────────────────────────────────────

class ActivityLog(models.Model):
    """Track user activity for security and audit purposes."""

    class ActionType(models.TextChoices):
        LOGIN            = 'login',            'Logged In'
        LOGOUT           = 'logout',           'Logged Out'
        PASSWORD_CHANGED = 'password_changed', 'Password Changed'
        PROFILE_UPDATED  = 'profile_updated',  'Profile Updated'
        CARD_CREATED     = 'card_created',     'Card Created'
        CARD_UPDATED     = 'card_updated',     'Card Updated'
        CARD_DELETED     = 'card_deleted',     'Card Deleted'
        SETTINGS_CHANGED = 'settings_changed', 'Settings Changed'

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action      = models.CharField(max_length=50, choices=ActionType.choices)
    description = models.CharField(max_length=255, blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    timestamp   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering     = ['-timestamp']
        verbose_name = 'Activity Log'
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"{self.user.username} — {self.action} at {self.timestamp}"


# ── Signals ───────────────────────────────────────────────────────────────────

def _unique_org_slug(base):
    """Return a slug derived from base that doesn't exist in Organization."""
    slug = slugify(base) or 'workspace'
    candidate = slug
    n = 1
    while Organization.objects.filter(slug=candidate).exists():
        candidate = f"{slug}-{n}"
        n += 1
    return candidate


@receiver(post_save, sender=User)
def create_personal_organization(sender, instance, created, **kwargs):
    """
    Auto-create a Free personal Organization for every new user and make
    them the owner. Existing cards (owner=user) are linked to this org
    retroactively by the data migration.
    """
    if not created:
        return
    # Skip if the user already has an org membership (e.g. accepted an invite
    # before their account was fully saved — edge case).
    if OrganizationMember.objects.filter(user=instance).exists():
        return

    full_name = instance.get_full_name() or instance.username
    org = Organization.objects.create(
        name=f"{full_name}'s Workspace",
        slug=_unique_org_slug(instance.username),
        plan=Plan.FREE,
    )
    OrganizationMember.objects.create(
        organization=org,
        user=instance,
        role=OrganizationMember.Role.OWNER,
        invite_accepted=True,
        invited_email=instance.email or '',
    )


@receiver(post_save, sender=User)
def create_user_settings(sender, instance, created, **kwargs):
    """Auto-create UserSettings for every new user."""
    if created:
        UserSettings.objects.get_or_create(user=instance)