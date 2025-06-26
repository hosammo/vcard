# cards/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Count, Q
from datetime import timedelta
import json
import vobject
import user_agents
from urllib.parse import urlparse
from collections import defaultdict, Counter
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from .models import BusinessCard, CardView, ContactDownload
from .auth_forms import CustomUserRegistrationForm, UserLoginForm, BusinessCardForm, PhoneNumberFormSet
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from .auth_forms import CustomUserRegistrationForm, UserLoginForm
from .auth_forms import CustomUserRegistrationForm, UserLoginForm, BusinessCardForm, PhoneNumberFormSet


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def home(request):
    """Home page - simple landing page"""
    return render(request, 'cards/home.html')


def get_location_from_ip(ip_address):
    """Get location data from IP address using free geolocation service"""
    try:
        import requests
        import json

        # Skip local/private IPs
        if ip_address in ['127.0.0.1', 'localhost'] or ip_address.startswith('192.168.') or ip_address.startswith(
                '10.'):
            return {
                'country': 'Local',
                'city': 'Development',
                'region': 'Local',
                'latitude': None,
                'longitude': None
            }

        # Use ip-api.com (free service, 1000 requests per month)
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return {
                    'country': data.get('country', ''),
                    'city': data.get('city', ''),
                    'region': data.get('regionName', ''),
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon')
                }
    except Exception as e:
        print(f"Geolocation error: {e}")

    return {
        'country': '',
        'city': '',
        'region': '',
        'latitude': None,
        'longitude': None
    }


def card_detail(request, url_slug):
    """Display a business card"""
    card = get_object_or_404(BusinessCard, custom_url=url_slug, is_active=True)

    # Get client IP and location data
    ip_address = get_client_ip(request)
    location_data = get_location_from_ip(ip_address)

    # Track the view with location data
    CardView.objects.create(
        card=card,
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        referer=request.META.get('HTTP_REFERER', ''),
        country=location_data['country'],
        city=location_data['city'],
        region=location_data['region'],
        latitude=location_data['latitude'],
        longitude=location_data['longitude'],
    )

    context = {
        'card': card,
    }
    return render(request, 'cards/card_detail.html', context)


def download_vcard(request, url_slug):
    """Download vCard file with complete phone numbers support"""
    try:
        card = get_object_or_404(BusinessCard, custom_url=url_slug, is_active=True)

        # Track the download
        ContactDownload.objects.create(
            card=card,
            ip_address=get_client_ip(request),
            download_type='vcard'
        )

        # Create vCard
        vcard = vobject.vCard()

        # Name
        vcard.add('fn')
        vcard.fn.value = card.full_name

        vcard.add('n')
        vcard.n.value = vobject.vcard.Name(
            family=card.last_name,
            given=card.first_name
        )

        # Contact details
        if card.email:
            vcard.add('email')
            vcard.email.value = card.email
            vcard.email.type_param = ['INTERNET']

        # FIXED: Handle multiple phone numbers properly
        phone_numbers = card.phone_numbers.all()
        if phone_numbers.exists():
            for phone in phone_numbers:
                tel = vcard.add('tel')
                tel.value = phone.full_number

                # Set phone type based on label
                type_params = []
                if phone.label == 'mobile':
                    type_params.append('CELL')
                elif phone.label == 'work':
                    type_params.append('WORK')
                elif phone.label == 'home':
                    type_params.append('HOME')
                elif phone.label == 'fax':
                    type_params.append('FAX')
                else:
                    type_params.append('VOICE')

                # Add primary designation
                if phone.is_primary:
                    type_params.append('PREF')

                # Add WhatsApp note if applicable
                if phone.is_whatsapp:
                    type_params.append('WHATSAPP')

                tel.type_param = type_params

        # Fallback to old phone field if no new phone numbers exist
        elif card.phone:
            tel = vcard.add('tel')
            tel.value = card.phone
            tel.type_param = ['CELL']

        if card.website:
            vcard.add('url')
            vcard.url.value = card.website

        # Organization
        if card.company:
            vcard.add('org')
            vcard.org.value = [card.company]

        if card.job_title:
            vcard.add('title')
            vcard.title.value = card.job_title

        # Address
        if card.address:
            vcard.add('adr')
            vcard.adr.value = vobject.vcard.Address(
                street=card.address
            )

        # Note/Bio with social media
        notes = []
        if card.bio:
            notes.append(card.bio)

        # Add social media URLs
        social_urls = []
        if card.linkedin_url:
            social_urls.append(f"LinkedIn: {card.linkedin_url}")
        if card.twitter_url:
            social_urls.append(f"Twitter: {card.twitter_url}")
        if card.instagram_url:
            social_urls.append(f"Instagram: {card.instagram_url}")
        if card.facebook_url:
            social_urls.append(f"Facebook: {card.facebook_url}")
        if card.portfolio_url:
            social_urls.append(f"Portfolio: {card.portfolio_url}")
        if card.custom_link_1_url and card.custom_link_1_title:
            social_urls.append(f"{card.custom_link_1_title}: {card.custom_link_1_url}")
        if card.custom_link_2_url and card.custom_link_2_title:
            social_urls.append(f"{card.custom_link_2_title}: {card.custom_link_2_url}")

        if social_urls:
            notes.append("Social Media:")
            notes.extend(social_urls)

        if notes:
            vcard.add('note')
            vcard.note.value = "\n".join(notes)

        # Generate response
        response = HttpResponse(
            vcard.serialize(),
            content_type='text/vcard; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="{card.first_name}_{card.last_name}.vcf"'

        return response

    except Exception as e:
        print(f"Error in download_vcard: {e}")
        import traceback
        traceback.print_exc()
        return HttpResponse(f"Error generating vCard: {str(e)}", status=500)

@csrf_exempt
def card_stats(request, url_slug):
    """API endpoint for card statistics"""
    card = get_object_or_404(BusinessCard, custom_url=url_slug)

    # Calculate stats
    total_views = card.views.count()
    total_downloads = card.downloads.count()

    # Recent views (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_views = card.views.filter(timestamp__gte=thirty_days_ago).count()
    recent_downloads = card.downloads.filter(timestamp__gte=thirty_days_ago).count()

    # Views by day (last 7 days)
    views_by_day = []
    for i in range(7):
        day = timezone.now() - timezone.timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timezone.timedelta(days=1)

        daily_views = card.views.filter(
            timestamp__gte=day_start,
            timestamp__lt=day_end
        ).count()

        views_by_day.append({
            'date': day.strftime('%Y-%m-%d'),
            'views': daily_views
        })

    return JsonResponse({
        'total_views': total_views,
        'total_downloads': total_downloads,
        'recent_views': recent_views,
        'recent_downloads': recent_downloads,
        'views_by_day': views_by_day,
    })



@login_required
def simple_card_statistics(request, card_id):
    """Simple statistics page - accessible by card owner or admin"""
    card = get_object_or_404(BusinessCard, id=card_id)

    # Check permissions: user must be the owner OR staff member
    if not (request.user.is_staff or card.owner == request.user):
        messages.error(request, "You don't have permission to view these statistics.")
        return redirect('user_dashboard')

    # Basic stats
    total_views = card.views.count()
    total_downloads = card.downloads.count()

    # Simple country count with flags
    countries = card.views.exclude(country='').values('country').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Add flags to countries
    country_flags = {
        'Kuwait': '🇰🇼',
        'United States': '🇺🇸',
        'United Kingdom': '🇬🇧',
        'Canada': '🇨🇦',
        'Germany': '🇩🇪',
        'France': '🇫🇷',
        'Italy': '🇮🇹',
        'Spain': '🇪🇸',
        'Netherlands': '🇳🇱',
        'Australia': '🇦🇺',
        'Japan': '🇯🇵',
        'South Korea': '🇰🇷',
        'China': '🇨🇳',
        'India': '🇮🇳',
        'Brazil': '🇧🇷',
        'Mexico': '🇲🇽',
        'Argentina': '🇦🇷',
        'Saudi Arabia': '🇸🇦',
        'United Arab Emirates': '🇦🇪',
        'Qatar': '🇶🇦',
        'Bahrain': '🇧🇭',
        'Oman': '🇴🇲',
        'Egypt': '🇪🇬',
        'Jordan': '🇯🇴',
        'Lebanon': '🇱🇧',
        'Turkey': '🇹🇷',
        'Russia': '🇷🇺',
        'Sweden': '🇸🇪',
        'Norway': '🇳🇴',
        'Denmark': '🇩🇰',
        'Finland': '🇫🇮',
        'Switzerland': '🇨🇭',
        'Austria': '🇦🇹',
        'Belgium': '🇧🇪',
        'Portugal': '🇵🇹',
        'Ireland': '🇮🇪',
        'Poland': '🇵🇱',
        'Czech Republic': '🇨🇿',
        'Hungary': '🇭🇺',
        'Greece': '🇬🇷',
        'South Africa': '🇿🇦',
        'Nigeria': '🇳🇬',
        'Kenya': '🇰🇪',
        'Morocco': '🇲🇦',
        'Israel': '🇮🇱',
        'Singapore': '🇸🇬',
        'Malaysia': '🇲🇾',
        'Thailand': '🇹🇭',
        'Philippines': '🇵🇭',
        'Indonesia': '🇮🇩',
        'Vietnam': '🇻🇳',
        'New Zealand': '🇳🇿',
        'Local': '🏠',
        'Development': '💻',
    }

    # Add flags to country data
    countries_with_flags = []
    for country in countries:
        country_name = country['country'] or 'Unknown'
        countries_with_flags.append({
            'country': country_name,
            'count': country['count'],
            'flag': country_flags.get(country_name, '🌍')  # Default flag if not found
        })

    # Recent views
    recent_views = card.views.order_by('-timestamp')[:20]

    # Daily views for the last 14 days
    from datetime import timedelta
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=14)

    daily_views = card.views.filter(
        timestamp__date__gte=start_date
    ).values('timestamp__date').annotate(
        views=Count('id')
    ).order_by('timestamp__date')

    # Convert to the format we need
    views_dict = {}
    for item in daily_views:
        date_key = item['timestamp__date'].strftime('%Y-%m-%d')
        views_dict[date_key] = item['views']

    chart_data = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        chart_data.append({
            'date': date_str,
            'views': views_dict.get(date_str, 0)
        })
        current_date += timedelta(days=1)

    context = {
        'card': card,
        'total_views': total_views,
        'total_downloads': total_downloads,
        'countries': countries_with_flags,
        'recent_views': recent_views,
        'chart_data': json.dumps(chart_data),
        'is_owner': card.owner == request.user,  # Add this to show if user is owner
    }

    return render(request, 'admin/cards/card_statistics.html', context)

def user_register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('user_login')
    else:
        form = CustomUserRegistrationForm()

    return render(request, 'auth/register.html', {'form': form})


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('user_dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()

    return render(request, 'auth/login.html', {'form': form})


def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


@login_required
def user_dashboard(request):
    """User dashboard - shows their business cards"""
    user_cards = request.user.business_cards.all().order_by('-created_at')

    context = {
        'user_cards': user_cards,
        'total_cards': user_cards.count(),
        'total_views': sum(card.views.count() for card in user_cards),
        'total_downloads': sum(card.downloads.count() for card in user_cards),
    }

    return render(request, 'auth/dashboard.html', context)


@login_required
def create_business_card(request):
    """Create a new business card with phone numbers"""
    if request.method == 'POST':
        form = BusinessCardForm(request.POST, request.FILES)
        phone_formset = PhoneNumberFormSet(request.POST, prefix='phones')

        if form.is_valid() and phone_formset.is_valid():
            card = form.save(commit=False)
            card.owner = request.user  # Set the owner to current user
            card.save()

            # Save phone numbers
            phone_formset.instance = card
            phone_formset.save()

            messages.success(request, f'Business card "{card.full_name}" created successfully!')
            return redirect('user_dashboard')
    else:
        # Pre-fill form with user data
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = BusinessCardForm(initial=initial_data)
        phone_formset = PhoneNumberFormSet(prefix='phones')

    return render(request, 'auth/create_card.html', {
        'form': form,
        'phone_formset': phone_formset
    })


@login_required
def edit_business_card(request, card_id):
    """Edit an existing business card with phone numbers"""
    card = get_object_or_404(BusinessCard, id=card_id, owner=request.user)

    if request.method == 'POST':
        form = BusinessCardForm(request.POST, request.FILES, instance=card)
        phone_formset = PhoneNumberFormSet(request.POST, instance=card, prefix='phones')

        if form.is_valid() and phone_formset.is_valid():
            form.save()
            phone_formset.save()
            messages.success(request, f'Business card "{card.full_name}" updated successfully!')
            return redirect('user_dashboard')
    else:
        form = BusinessCardForm(instance=card)
        phone_formset = PhoneNumberFormSet(instance=card, prefix='phones')

    return render(request, 'auth/edit_card.html', {
        'form': form,
        'phone_formset': phone_formset,
        'card': card
    })


@login_required
def delete_business_card(request, card_id):
    """Delete a business card"""
    card = get_object_or_404(BusinessCard, id=card_id, owner=request.user)

    if request.method == 'POST':
        card_name = card.full_name
        card.delete()
        messages.success(request, f'Business card "{card_name}" deleted successfully!')
        return redirect('user_dashboard')

    return render(request, 'auth/delete_card.html', {'card': card})
