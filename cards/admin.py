# cards/admin.py - Clean Complete Version
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import BusinessCard, CardView, ContactDownload, CountryCode, PhoneNumber
from .forms import BusinessCardAdminForm, PhoneNumberAdminForm


class PhoneNumberInline(admin.TabularInline):
    model = PhoneNumber
    form = PhoneNumberAdminForm
    extra = 1
    fields = ['label', 'country_code', 'number', 'is_primary', 'is_whatsapp']


@admin.register(CountryCode)
class CountryCodeAdmin(admin.ModelAdmin):
    list_display = ['flag_emoji', 'country_name', 'country_code', 'iso_code']
    list_filter = ['country_code']
    search_fields = ['country_name', 'country_code', 'iso_code']
    ordering = ['country_name']


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    form = PhoneNumberAdminForm
    list_display = ['business_card', 'formatted_number', 'label', 'is_primary', 'is_whatsapp']
    list_filter = ['label', 'is_primary', 'is_whatsapp', 'country_code']
    search_fields = ['business_card__first_name', 'business_card__last_name', 'number']


@admin.register(BusinessCard)
class BusinessCardAdmin(admin.ModelAdmin):
    form = BusinessCardAdminForm
    list_display = [
        'full_name', 'profile_type', 'email', 'primary_phone_display',
        'view_count', 'download_count', 'is_active', 'created_at'
    ]
    list_filter = ['profile_type', 'is_active', 'created_at']
    search_fields = ['first_name', 'last_name', 'email', 'company']
    readonly_fields = ['id', 'created_at', 'updated_at', 'qr_code_preview', 'card_url', 'color_preview']
    inlines = [PhoneNumberInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('profile_type', 'first_name', 'last_name', 'custom_url')
        }),
        ('Professional Details', {
            'fields': ('job_title', 'company', 'bio', 'skills')
        }),
        ('Contact Information', {
            'fields': ('email', 'website', 'address'),
            'description': 'Phone numbers are managed in the Phone Numbers section below.'
        }),
        ('Images & Banner', {
            'fields': ('profile_photo', 'company_logo', 'banner_image', 'banner_text', 'qr_code_preview')
        }),
        ('UI Customization', {
            'fields': ('background_color', 'accent_color', 'text_color', 'color_preview'),
            'description': '''
                <div style="background: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 10px;">
                    <strong>🎨 Customize your business card colors:</strong><br/>
                    • <strong>Background Color:</strong> Primary gradient start color<br/>
                    • <strong>Accent Color:</strong> Secondary gradient end color<br/>
                    • <strong>Text Color:</strong> Text color for the hero section<br/>
                    <em>Changes preview in real-time as you pick colors!</em>
                </div>
            '''
        }),
        ('Social Media', {
            'fields': ('linkedin_url', 'twitter_url', 'instagram_url', 'facebook_url'),
            'classes': ('collapse',)
        }),
        ('Custom Links', {
            'fields': (
                'portfolio_url',
                'custom_link_1_title', 'custom_link_1_url',
                'custom_link_2_title', 'custom_link_2_url'
            ),
            'classes': ('collapse',)
        }),
        ('Settings & Info', {
            'fields': ('is_active', 'card_url', 'id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def primary_phone_display(self, obj):
        primary = obj.primary_phone
        if primary:
            return primary.formatted_number
        return "No primary phone"

    primary_phone_display.short_description = "Primary Phone"


    def view_count(self, obj):
        count = obj.views.count()
        if count > 0:
            # Simple clickable link to statistics
            url = f"/statistics/{obj.id}/"
            return format_html(
                '<a href="{}" style="color: #0066cc; text-decoration: none;">{} views</a>',
                url, count
            )
        return "0 views"

    view_count.short_description = "Views"

    view_count.short_description = "Views"

    def download_count(self, obj):
        return obj.downloads.count()

    download_count.short_description = "Downloads"

    def qr_code_preview(self, obj):
        if obj.qr_code:
            return format_html(
                '<img src="{}" width="100" height="100" />',
                obj.qr_code.url
            )
        return "No QR Code"

    qr_code_preview.short_description = "QR Code"

    def color_preview(self, obj):
        return format_html(
            '<div id="live-color-preview" style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; background: white; padding: 10px; border-radius: 6px; border: 1px solid #e0e0e0;">'
            '<div class="color-item" style="display: flex; flex-direction: column; align-items: center; gap: 5px;">'
            '<div class="bg-preview" style="width: 40px; height: 30px; background: {}; border: 1px solid #ccc; border-radius: 4px;" title="Background: {}"></div>'
            '<small class="bg-code" style="font-family: monospace; font-size: 10px; color: #666; font-weight: bold;">{}</small>'
            '</div>'
            '<div class="color-item" style="display: flex; flex-direction: column; align-items: center; gap: 5px;">'
            '<div class="accent-preview" style="width: 40px; height: 30px; background: {}; border: 1px solid #ccc; border-radius: 4px;" title="Accent: {}"></div>'
            '<small class="accent-code" style="font-family: monospace; font-size: 10px; color: #666; font-weight: bold;">{}</small>'
            '</div>'
            '<div class="color-item" style="display: flex; flex-direction: column; align-items: center; gap: 5px;">'
            '<div class="text-preview" style="width: 40px; height: 30px; background: {}; border: 1px solid #ccc; border-radius: 4px;" title="Text: {}"></div>'
            '<small class="text-code" style="font-family: monospace; font-size: 10px; color: #666; font-weight: bold;">{}</small>'
            '</div>'
            '<div class="color-item" style="display: flex; flex-direction: column; align-items: center; gap: 5px;">'
            '<div class="gradient-preview" style="width: 80px; height: 30px; background: {}; border: 1px solid #ccc; border-radius: 4px; position: relative; display: flex; align-items: center; justify-content: center;" title="Gradient Preview">'
            '<span style="font-size: 9px; color: white; text-shadow: 0 0 3px rgba(0,0,0,0.8); font-weight: bold; letter-spacing: 0.5px;">LIVE</span>'
            '</div>'
            '<small style="font-size: 10px; color: #666; font-weight: bold;">Gradient</small>'
            '</div>'
            '</div>',
            obj.background_color, obj.background_color, obj.background_color.upper(),
            obj.accent_color, obj.accent_color, obj.accent_color.upper(),
            obj.text_color, obj.text_color, obj.text_color.upper(),
            obj.gradient_style
        )

    color_preview.short_description = "Color Scheme"

    def card_url(self, obj):
        if obj.custom_url:
            url = obj.get_full_url()
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                url, url
            )
        return "Not available"

    card_url.short_description = "Card URL"

    actions = ['activate_cards', 'deactivate_cards', 'regenerate_qr_codes']

    def activate_cards(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Activated {queryset.count()} cards.")

    activate_cards.short_description = "Activate selected cards"

    def deactivate_cards(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {queryset.count()} cards.")

    deactivate_cards.short_description = "Deactivate selected cards"

    def regenerate_qr_codes(self, request, queryset):
        for card in queryset:
            if card.qr_code:
                card.qr_code.delete()
            card.generate_qr_code()
        self.message_user(request, f"Regenerated QR codes for {queryset.count()} cards.")

    regenerate_qr_codes.short_description = "Regenerate QR codes"


@admin.register(CardView)
class CardViewAdmin(admin.ModelAdmin):
    list_display = ['card', 'ip_address', 'timestamp', 'country', 'city', 'user_agent_short']
    list_filter = ['timestamp', 'country', 'city']
    search_fields = ['card__first_name', 'card__last_name', 'ip_address', 'country', 'city']
    readonly_fields = ['card', 'ip_address', 'user_agent', 'referer', 'timestamp', 'country', 'city']
    date_hierarchy = 'timestamp'

    def user_agent_short(self, obj):
        if obj.user_agent:
            return obj.user_agent[:50] + "..." if len(obj.user_agent) > 50 else obj.user_agent
        return ""

    user_agent_short.short_description = "User Agent"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ContactDownload)
class ContactDownloadAdmin(admin.ModelAdmin):
    list_display = ['card', 'download_type', 'ip_address', 'timestamp']
    list_filter = ['download_type', 'timestamp']
    search_fields = ['card__first_name', 'card__last_name', 'ip_address']
    readonly_fields = ['card', 'ip_address', 'download_type', 'timestamp']
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Customize admin site
admin.site.site_header = "Virtual Business Cards Admin"
admin.site.site_title = "VCard Admin"
admin.site.index_title = "Manage Your Business Cards"