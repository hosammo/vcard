# cards/views.py
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import BusinessCard, CardView, ContactDownload
import vobject


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
    """Download vCard file"""
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

    if card.phone:
        vcard.add('tel')
        vcard.tel.value = card.phone
        vcard.tel.type_param = ['CELL']

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

    # Note/Bio
    if card.bio:
        vcard.add('note')
        vcard.note.value = card.bio

    # Generate response
    response = HttpResponse(
        vcard.serialize(),
        content_type='text/vcard; charset=utf-8'
    )
    response['Content-Disposition'] = f'attachment; filename="{card.first_name}_{card.last_name}.vcf"'

    return response


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


# Add these views to cards/views.py

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import json


@staff_member_required
def card_statistics(request, card_id):
    """Detailed statistics for a specific card"""
    card = get_object_or_404(BusinessCard, id=card_id)

    # Time periods
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Basic stats
    total_views = card.views.count()
    total_downloads = card.downloads.count()

    # Time-based stats
    today_views = card.views.filter(timestamp__date=today).count()
    week_views = card.views.filter(timestamp__date__gte=week_ago).count()
    month_views = card.views.filter(timestamp__date__gte=month_ago).count()

    # Location stats
    country_stats = card.views.values('country').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    city_stats = card.views.values('city', 'country').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Daily views for the last 30 days
    daily_views = []
    for i in range(30):
        date = today - timedelta(days=i)
        views = card.views.filter(timestamp__date=date).count()
        daily_views.append({
            'date': date.strftime('%Y-%m-%d'),
            'views': views
        })
    daily_views.reverse()

    # Recent views with location
    recent_views = card.views.select_related().order_by('-timestamp')[:20]

    context = {
        'card': card,
        'total_views': total_views,
        'total_downloads': total_downloads,
        'today_views': today_views,
        'week_views': week_views,
        'month_views': month_views,
        'country_stats': country_stats,
        'city_stats': city_stats,
        'daily_views': json.dumps(daily_views),
        'recent_views': recent_views,
    }

    return render(request, 'admin/cards/card_statistics.html', context)


@staff_member_required
def global_statistics(request):
    """Global statistics across all cards"""
    # Total stats
    total_cards = BusinessCard.objects.filter(is_active=True).count()
    total_views = CardView.objects.count()
    total_downloads = ContactDownload.objects.count()

    # Time-based stats
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    today_views = CardView.objects.filter(timestamp__date=today).count()
    week_views = CardView.objects.filter(timestamp__date__gte=week_ago).count()
    month_views = CardView.objects.filter(timestamp__date__gte=month_ago).count()

    # Top cards by views
    top_cards = BusinessCard.objects.annotate(
        view_count=Count('views')
    ).order_by('-view_count')[:10]

    # Geographic distribution
    country_distribution = CardView.objects.values('country').annotate(
        count=Count('id')
    ).order_by('-count')[:15]

    # Recent activity
    recent_views = CardView.objects.select_related('card').order_by('-timestamp')[:20]

    context = {
        'total_cards': total_cards,
        'total_views': total_views,
        'total_downloads': total_downloads,
        'today_views': today_views,
        'week_views': week_views,
        'month_views': month_views,
        'top_cards': top_cards,
        'country_distribution': country_distribution,
        'recent_views': recent_views,
    }

    return render(request, 'admin/cards/global_statistics.html', context)