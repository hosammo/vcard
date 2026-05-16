# cards/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Count, Q
from datetime import timedelta, date
from dateutil.relativedelta import relativedelta
import json
import csv
import vobject
import user_agents
from urllib.parse import urlparse
from collections import defaultdict, Counter
from .models import BusinessCard, CardView, ContactDownload, CardInteraction, CardLead, Organization, OrganizationMember, Plan, UserSettings, ActivityLog
from .auth_forms import CustomUserRegistrationForm, UserLoginForm, BusinessCardForm, PhoneNumberFormSet


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_device_type(user_agent_string):
    """Parse user-agent string into Mobile / Tablet / Desktop"""
    ua = (user_agent_string or '').lower()
    if 'ipad' in ua or ('android' in ua and 'mobile' not in ua) or 'tablet' in ua:
        return 'Tablet'
    if 'mobile' in ua or 'android' in ua or 'iphone' in ua or 'ipod' in ua:
        return 'Mobile'
    return 'Desktop'


def get_referer_source(referer):
    """Classify a referrer URL into a human-readable source label"""
    if not referer:
        return 'Direct'
    r = referer.lower()
    for keyword, label in [
        ('linkedin',   'LinkedIn'),
        ('google',     'Google'),
        ('twitter',    'Twitter/X'),
        ('x.com',      'Twitter/X'),
        ('facebook',   'Facebook'),
        ('instagram',  'Instagram'),
        ('whatsapp',   'WhatsApp'),
        ('t.me',       'Telegram'),
    ]:
        if keyword in r:
            return label
    return 'Other'


def log_activity(user, action, description='', request=None):
    """Record a user activity log entry."""
    ip = get_client_ip(request) if request else None
    ActivityLog.objects.create(
        user=user,
        action=action,
        description=description,
        ip_address=ip,
    )


# ── Organization helpers ──────────────────────────────────────────────────────

def get_user_org(user):
    """
    Return the user's primary Organization — the one where they are the owner,
    or the first accepted membership if no owner role exists.
    """
    memberships = user.org_memberships.filter(
        invite_accepted=True
    ).select_related('organization').order_by('joined_at')

    # Prefer the org where they are owner
    for m in memberships:
        if m.role == OrganizationMember.Role.OWNER:
            return m.organization
    first = memberships.first()
    return first.organization if first else None


def get_user_membership(user, card):
    """Return OrganizationMember for user in card's org, or None."""
    if not card.organization:
        return None
    return card.organization.get_member(user)


def can_access_card(user, card, require_edit=False):
    """
    Return True if user may access the card.
    Staff always can. Otherwise the user must be an accepted member of
    the card's organization. If require_edit=True the member must also
    have edit permission (owner / admin / editor).
    """
    if user.is_staff:
        return True
    if not card.organization:
        # Legacy fallback while owner field still exists
        return card.owner == user
    member = card.organization.get_member(user)
    if not member:
        return False
    if require_edit:
        return member.can_edit
    return True


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



@csrf_exempt
@require_POST
def track_interaction(request):
    """Record a single link/button click on a public business card"""
    try:
        data = json.loads(request.body)
        card = BusinessCard.objects.get(id=data['card_id'])
        interaction_type = data.get('interaction_type', 'unknown')
        CardInteraction.objects.create(
            card=card,
            interaction_type=interaction_type,
            ip_address=get_client_ip(request),
        )
        return JsonResponse({'status': 'ok'})
    except Exception:
        return JsonResponse({'status': 'error'}, status=400)


@login_required
def export_statistics_csv(request, card_id):
    """Export card view history as a CSV download (max 500 rows)."""
    card = get_object_or_404(BusinessCard, id=card_id)
    if not can_access_card(request.user, card):
        messages.error(request, "You don't have permission to export these statistics.")
        return redirect('user_dashboard')

    # Feature gate: CSV export locked for Free plan
    if card.organization and not card.organization.has_csv_export:
        messages.warning(
            request,
            "CSV export is available on Pro and Business plans. Upgrade to unlock this feature."
        )
        return redirect('upgrade_plan')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="stats_{card.custom_url}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Timestamp', 'Country', 'City', 'Region', 'IP Address', 'Device', 'Referrer Source'])
    for v in card.views.order_by('-timestamp')[:500]:
        writer.writerow([
            v.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            v.country,
            v.city,
            v.region,
            v.ip_address,
            get_device_type(v.user_agent),
            get_referer_source(v.referer),
        ])
    return response


# Country → emoji flag mapping (used by statistics view)
COUNTRY_FLAGS = {
    'Kuwait': '🇰🇼', 'United States': '🇺🇸', 'United Kingdom': '🇬🇧',
    'Canada': '🇨🇦', 'Germany': '🇩🇪', 'France': '🇫🇷', 'Italy': '🇮🇹',
    'Spain': '🇪🇸', 'Netherlands': '🇳🇱', 'Australia': '🇦🇺', 'Japan': '🇯🇵',
    'South Korea': '🇰🇷', 'China': '🇨🇳', 'India': '🇮🇳', 'Brazil': '🇧🇷',
    'Mexico': '🇲🇽', 'Argentina': '🇦🇷', 'Saudi Arabia': '🇸🇦',
    'United Arab Emirates': '🇦🇪', 'Qatar': '🇶🇦', 'Bahrain': '🇧🇭',
    'Oman': '🇴🇲', 'Egypt': '🇪🇬', 'Jordan': '🇯🇴', 'Lebanon': '🇱🇧',
    'Turkey': '🇹🇷', 'Russia': '🇷🇺', 'Sweden': '🇸🇪', 'Norway': '🇳🇴',
    'Denmark': '🇩🇰', 'Finland': '🇫🇮', 'Switzerland': '🇨🇭', 'Austria': '🇦🇹',
    'Belgium': '🇧🇪', 'Portugal': '🇵🇹', 'Ireland': '🇮🇪', 'Poland': '🇵🇱',
    'Czech Republic': '🇨🇿', 'Hungary': '🇭🇺', 'Greece': '🇬🇷',
    'South Africa': '🇿🇦', 'Nigeria': '🇳🇬', 'Kenya': '🇰🇪', 'Morocco': '🇲🇦',
    'Israel': '🇮🇱', 'Singapore': '🇸🇬', 'Malaysia': '🇲🇾', 'Thailand': '🇹🇭',
    'Philippines': '🇵🇭', 'Indonesia': '🇮🇩', 'Vietnam': '🇻🇳',
    'New Zealand': '🇳🇿', 'Local': '🏠', 'Development': '💻',
}


PLAN_PRICES = {
    Plan.PRO:      '$9 / month',
    Plan.BUSINESS: '$29 / month',
}

PLAN_LABELS = {
    Plan.PRO:      'Pro',
    Plan.BUSINESS: 'Business',
}


@login_required
def upgrade_plan(request):
    """Upgrade / pricing page."""
    org = get_user_org(request.user)
    return render(request, 'auth/upgrade.html', {
        'org':          org,
        'has_paid_plan': org and org.plan != Plan.FREE,
    })


@login_required
def simulate_payment(request, plan):
    """
    Payment simulator — stands in for a real checkout until a payment
    provider is chosen.  GET shows a fake card form; POST confirms and
    applies the plan.
    """
    if plan not in (Plan.PRO, Plan.BUSINESS):
        messages.error(request, "Invalid plan.")
        return redirect('upgrade_plan')

    org = get_user_org(request.user)
    if not org:
        messages.error(request, "No organisation found for your account.")
        return redirect('upgrade_plan')

    if request.method == 'POST':
        # Simulate successful payment — apply the plan immediately
        org.plan = plan
        org.save(update_fields=['plan'])
        messages.success(
            request,
            f"🎉 You're now on the {PLAN_LABELS[plan]} plan! "
            "All features are unlocked — enjoy."
        )
        return redirect('user_dashboard')

    return render(request, 'auth/simulate_payment.html', {
        'org':        org,
        'plan':       plan,
        'plan_label': PLAN_LABELS[plan],
        'plan_price': PLAN_PRICES[plan],
    })


@login_required
@require_POST
def simulate_downgrade(request):
    """
    Simulator: immediately downgrade the org back to the Free plan.
    (Replaces the billing-portal cancel flow during development.)
    """
    org = get_user_org(request.user)
    if org:
        org.plan = Plan.FREE
        org.save(update_fields=['plan'])
        messages.info(request, "Your plan has been downgraded to Free.")
    return redirect('upgrade_plan')


@login_required
def simple_card_statistics(request, card_id):
    """Enhanced statistics page — accessible by card owner or staff"""
    card = get_object_or_404(BusinessCard, id=card_id)

    if not can_access_card(request.user, card):
        messages.error(request, "You don't have permission to view these statistics.")
        return redirect('user_dashboard')

    # Feature gate: analytics locked for Free plan
    if card.organization and not card.organization.has_analytics:
        messages.warning(
            request,
            "Analytics are available on Pro and Business plans. Upgrade to unlock this feature."
        )
        return redirect('upgrade_plan')

    # ── Date range ────────────────────────────────────────────────────────────
    try:
        days = int(request.GET.get('days', 14))
        if days not in (7, 14, 30, 90):
            days = 14
    except (ValueError, TypeError):
        days = 14

    now       = timezone.now()
    end_dt    = now
    start_dt  = now - timedelta(days=days)
    prev_start = now - timedelta(days=days * 2)

    # ── Overall totals ────────────────────────────────────────────────────────
    total_views     = card.views.count()
    total_downloads = card.downloads.count()

    # ── Period counts (for trend calculation) ─────────────────────────────────
    period_views     = card.views.filter(timestamp__gte=start_dt).count()
    period_downloads = card.downloads.filter(timestamp__gte=start_dt).count()
    prev_views       = card.views.filter(timestamp__gte=prev_start, timestamp__lt=start_dt).count()
    prev_downloads   = card.downloads.filter(timestamp__gte=prev_start, timestamp__lt=start_dt).count()

    def pct_change(current, previous):
        if previous == 0:
            return None  # no previous data → no trend to show
        return round((current - previous) / previous * 100)

    trend_views     = pct_change(period_views, prev_views)
    trend_downloads = pct_change(period_downloads, prev_downloads)

    # ── Countries ─────────────────────────────────────────────────────────────
    countries_qs = (
        card.views
        .filter(timestamp__gte=start_dt)
        .exclude(country='')
        .values('country')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    countries_with_flags = [
        {'country': c['country'], 'count': c['count'],
         'flag': COUNTRY_FLAGS.get(c['country'], '🌍')}
        for c in countries_qs
    ]

    # ── Cities ────────────────────────────────────────────────────────────────
    cities_qs = (
        card.views
        .filter(timestamp__gte=start_dt)
        .exclude(city='')
        .values('city', 'country')
        .annotate(count=Count('id'))
        .order_by('-count')[:8]
    )
    cities = [
        {'city': c['city'], 'country': c['country'],
         'flag': COUNTRY_FLAGS.get(c['country'], '🌍'), 'count': c['count']}
        for c in cities_qs
    ]

    # ── Device breakdown ──────────────────────────────────────────────────────
    device_counter = Counter()
    for ua in card.views.filter(timestamp__gte=start_dt).values_list('user_agent', flat=True):
        device_counter[get_device_type(ua)] += 1
    device_breakdown = [
        {'device': d, 'count': device_counter[d]}
        for d in ['Mobile', 'Desktop', 'Tablet']
    ]

    # ── Referrer / source breakdown ───────────────────────────────────────────
    referer_counter = Counter()
    for ref in card.views.filter(timestamp__gte=start_dt).values_list('referer', flat=True):
        referer_counter[get_referer_source(ref)] += 1
    referer_breakdown = [
        {'source': src, 'count': cnt}
        for src, cnt in referer_counter.most_common()
    ]

    # ── Hourly distribution ───────────────────────────────────────────────────
    hourly_counter = Counter()
    for ts in card.views.filter(timestamp__gte=start_dt).values_list('timestamp', flat=True):
        hourly_counter[ts.hour] += 1
    hourly_data = [hourly_counter.get(h, 0) for h in range(24)]

    # ── Best day ──────────────────────────────────────────────────────────────
    best_day_qs = (
        card.views
        .values('timestamp__date')
        .annotate(count=Count('id'))
        .order_by('-count')
        .first()
    )
    best_day = None
    if best_day_qs and best_day_qs['count'] > 0:
        best_day = {
            'date':  best_day_qs['timestamp__date'].strftime('%b %d, %Y'),
            'views': best_day_qs['count'],
        }

    # ── Interaction counts ────────────────────────────────────────────────────
    interaction_qs = (
        card.interactions
        .filter(timestamp__gte=start_dt)
        .values('interaction_type')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    interaction_label_map = dict(CardInteraction.INTERACTION_TYPES)
    interaction_counts = [
        {'type': i['interaction_type'],
         'label': interaction_label_map.get(i['interaction_type'], i['interaction_type']),
         'count': i['count']}
        for i in interaction_qs
    ]

    # ── Recent views ──────────────────────────────────────────────────────────
    recent_views = card.views.order_by('-timestamp')[:20]

    # ── Daily chart data ──────────────────────────────────────────────────────
    end_date   = now.date()
    start_date = end_date - timedelta(days=days)

    daily_views_qs = (
        card.views
        .filter(timestamp__date__gte=start_date)
        .values('timestamp__date')
        .annotate(views=Count('id'))
        .order_by('timestamp__date')
    )
    views_dict = {
        item['timestamp__date'].strftime('%Y-%m-%d'): item['views']
        for item in daily_views_qs
    }
    chart_data = []
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        chart_data.append({'date': date_str, 'views': views_dict.get(date_str, 0)})
        current_date += timedelta(days=1)

    # ── Save rate % ───────────────────────────────────────────────────────────
    save_rate = round(total_downloads / total_views * 100) if total_views > 0 else 0

    context = {
        'card':                card,
        'days':                days,
        'total_views':         total_views,
        'total_downloads':     total_downloads,
        'save_rate':           save_rate,
        'period_views':        period_views,
        'period_downloads':    period_downloads,
        'trend_views':         trend_views,
        'trend_downloads':     trend_downloads,
        'countries':           countries_with_flags,
        'cities':              cities,
        'device_breakdown':    device_breakdown,
        'referer_breakdown':   referer_breakdown,
        'hourly_data':         json.dumps(hourly_data),
        'best_day':            best_day,
        'interaction_counts':  interaction_counts,
        'recent_views':        recent_views,
        'chart_data':          json.dumps(chart_data),
        'is_owner':            get_user_membership(request.user, card) is not None,
        'user_member':         get_user_membership(request.user, card),
    }

    return render(request, 'admin/cards/card_statistics.html', context)

def user_register(request):
    """User registration view"""
    from django.utils.http import url_has_allowed_host_and_scheme

    invite_email = request.GET.get('email', '').strip().lower()
    next_url     = request.GET.get('next', '').strip()

    if request.user.is_authenticated:
        return redirect(next_url if url_has_allowed_host_and_scheme(next_url, request.get_host()) else 'user_dashboard')

    if request.method == 'POST':
        next_url = request.POST.get('next', '').strip()
        form = CustomUserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name or user.username}! Your account is ready.')
            if next_url and url_has_allowed_host_and_scheme(next_url, request.get_host()):
                return redirect(next_url)
            return redirect('user_dashboard')
    else:
        initial = {}
        if invite_email:
            initial['email'] = invite_email
        form = CustomUserRegistrationForm(initial=initial)

    return render(request, 'auth/register.html', {
        'form':         form,
        'invite_email': invite_email,
        'next':         next_url,
    })


def user_login(request):
    """User login view"""
    from django.utils.http import url_has_allowed_host_and_scheme

    next_url = request.GET.get('next', '').strip()

    if request.user.is_authenticated:
        return redirect(next_url if url_has_allowed_host_and_scheme(next_url, request.get_host()) else 'user_dashboard')

    if request.method == 'POST':
        from django.contrib.auth import get_user_model
        next_url = request.POST.get('next', '').strip()
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email    = form.cleaned_data['email'].lower()
            password = form.cleaned_data['password']
            # Look up the user by email then authenticate with their username
            try:
                user_obj = get_user_model().objects.get(email__iexact=email)
                user = authenticate(request, username=user_obj.username, password=password)
            except get_user_model().DoesNotExist:
                user = None
            if user is not None:
                login(request, user)
                log_activity(user, ActivityLog.ActionType.LOGIN,
                             description='Logged in successfully', request=request)
                if next_url and url_has_allowed_host_and_scheme(next_url, request.get_host()):
                    return redirect(next_url)
                return redirect('user_dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()

    return render(request, 'auth/login.html', {'form': form, 'next': next_url})


def user_logout(request):
    """User logout view — supports ?next= for redirect after logout (e.g. invite page)."""
    from django.utils.http import url_has_allowed_host_and_scheme
    next_url = request.GET.get('next', '').strip()
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    if next_url and url_has_allowed_host_and_scheme(next_url, request.get_host()):
        return redirect(next_url)
    return redirect('home')


@login_required
def edit_profile(request):
    """Full account settings — Profile / Security / Notifications / Privacy / Activity."""
    from django.contrib.auth import update_session_auth_hash, get_user_model
    from django.urls import reverse

    user = request.user
    settings_obj, _ = UserSettings.objects.get_or_create(user=user)
    active_tab = request.GET.get('tab', 'profile')

    def _tab_redirect(tab, error=None):
        if error:
            messages.error(request, error)
        url = f"{reverse('edit_profile')}?tab={tab}"
        return redirect(url)

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Profile info ────────────────────────────────────────────────────
        if action == 'profile':
            first_name = request.POST.get('first_name', '').strip()
            last_name  = request.POST.get('last_name', '').strip()
            email      = request.POST.get('email', '').strip().lower()

            if not first_name or not last_name:
                return _tab_redirect('profile', 'First and last name are required.')
            if not email or '@' not in email:
                return _tab_redirect('profile', 'Please enter a valid email address.')
            if get_user_model().objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
                return _tab_redirect('profile', 'That email address is already in use.')

            user.first_name = first_name
            user.last_name  = last_name
            user.email      = email
            user.save(update_fields=['first_name', 'last_name', 'email'])
            log_activity(user, ActivityLog.ActionType.PROFILE_UPDATED,
                         'Profile information updated', request)
            messages.success(request, 'Profile updated successfully.')
            return _tab_redirect('profile')

        # ── Change password ──────────────────────────────────────────────────
        elif action == 'password':
            current_pw = request.POST.get('current_password', '')
            new_pw     = request.POST.get('new_password', '')
            confirm_pw = request.POST.get('confirm_password', '')

            if not user.check_password(current_pw):
                return _tab_redirect('security', 'Current password is incorrect.')
            if len(new_pw) < 8:
                return _tab_redirect('security', 'New password must be at least 8 characters.')
            if new_pw != confirm_pw:
                return _tab_redirect('security', 'New passwords do not match.')

            user.set_password(new_pw)
            user.save()
            update_session_auth_hash(request, user)
            log_activity(user, ActivityLog.ActionType.PASSWORD_CHANGED,
                         'Password changed', request)
            messages.success(request, 'Password changed successfully.')
            return _tab_redirect('security')

        # ── Notification settings ────────────────────────────────────────────
        elif action == 'notifications':
            settings_obj.email_notifications            = 'email_notifications' in request.POST
            settings_obj.card_view_alerts               = 'card_view_alerts' in request.POST
            settings_obj.contact_download_notifications = 'contact_download_notifications' in request.POST
            settings_obj.marketing_emails               = 'marketing_emails' in request.POST
            settings_obj.weekly_reports                 = 'weekly_reports' in request.POST
            settings_obj.billing_updates                = 'billing_updates' in request.POST
            settings_obj.save()
            log_activity(user, ActivityLog.ActionType.SETTINGS_CHANGED,
                         'Notification preferences updated', request)
            messages.success(request, 'Notification preferences saved.')
            return _tab_redirect('notifications')

        # ── Privacy settings ─────────────────────────────────────────────────
        elif action == 'privacy':
            settings_obj.public_profile         = 'public_profile' in request.POST
            settings_obj.search_engine_indexing = 'search_engine_indexing' in request.POST
            settings_obj.analytics_tracking     = 'analytics_tracking' in request.POST
            settings_obj.data_sharing           = 'data_sharing' in request.POST
            settings_obj.save()
            log_activity(user, ActivityLog.ActionType.SETTINGS_CHANGED,
                         'Privacy settings updated', request)
            messages.success(request, 'Privacy settings saved.')
            return _tab_redirect('privacy')

        # ── Delete account ───────────────────────────────────────────────────
        elif action == 'delete_account':
            confirm_text = request.POST.get('confirm_text', '').strip()
            if confirm_text != 'DELETE':
                return _tab_redirect('security', 'Type DELETE (in capitals) to confirm.')
            # Log before deleting so the record is written while the user still exists
            ActivityLog.objects.create(
                user=user,
                action=ActivityLog.ActionType.PROFILE_UPDATED,
                description='Account deleted by user',
                ip_address=get_client_ip(request),
            )
            logout(request)
            user.delete()
            messages.success(request, 'Your account has been permanently deleted.')
            return redirect('home')

    # Build activity log (last 20 entries)
    activity_logs = user.activity_logs.all()[:20]

    return render(request, 'auth/profile.html', {
        'profile_user':  user,
        'user_settings': settings_obj,
        'activity_logs': activity_logs,
        'active_tab':    active_tab,
    })


@login_required
def user_dashboard(request):
    """User dashboard — shows cards from all orgs the user belongs to."""
    # Collect cards across every org the user is a member of
    org_ids = request.user.org_memberships.filter(
        invite_accepted=True
    ).values_list('organization_id', flat=True)
    user_cards = BusinessCard.objects.filter(
        organization_id__in=org_ids
    ).order_by('-created_at')

    # Primary org (for plan info, limits, team counts)
    org    = get_user_org(request.user)
    member = org.get_member(request.user) if org else None

    context = {
        'user_cards':       user_cards,
        'total_cards':      user_cards.count(),
        'total_views':      sum(card.views.count() for card in user_cards),
        'total_downloads':  sum(card.downloads.count() for card in user_cards),
        # Org / plan context
        'org':              org,
        'org_member':       member,
        'can_add_card':     org.can_add_card if org else False,
        'card_limit':       org.card_limit   if org else 1,
        'plan':             org.plan         if org else 'free',
        'seat_count':       org.seat_count   if org else 1,
        'seat_limit':       org.seat_limit   if org else 1,
    }

    return render(request, 'auth/dashboard.html', context)


@login_required
def create_business_card(request):
    """Create a new business card with phone numbers."""
    org = get_user_org(request.user)

    # ── Plan limit check ────────────────────────────────────────────────────
    if org and not org.can_add_card:
        messages.error(
            request,
            f'You have reached the card limit ({org.card_limit}) for your '
            f'{org.get_plan_display() if hasattr(org, "get_plan_display") else org.plan.title()} plan. '
            f'Upgrade to add more cards.'
        )
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = BusinessCardForm(request.POST, request.FILES)
        phone_formset = PhoneNumberFormSet(request.POST, prefix='phones')

        if form.is_valid() and phone_formset.is_valid():
            card = form.save(commit=False)
            card.owner        = request.user  # legacy — kept during 1B
            card.organization = org           # primary ownership
            card.save()

            phone_formset.instance = card
            phone_formset.save()

            messages.success(request, f'Business card "{card.full_name}" created successfully!')
            return redirect('user_dashboard')
    else:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name':  request.user.last_name,
            'email':      request.user.email,
        }
        form = BusinessCardForm(initial=initial_data)
        phone_formset = PhoneNumberFormSet(prefix='phones')

    return render(request, 'auth/create_card.html', {
        'form':          form,
        'phone_formset': phone_formset,
        'org':           org,
    })


@login_required
def edit_business_card(request, card_id):
    """Edit an existing business card with phone numbers."""
    card = get_object_or_404(BusinessCard, id=card_id)
    if not can_access_card(request.user, card, require_edit=True):
        messages.error(request, "You don't have permission to edit this card.")
        return redirect('user_dashboard')

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
    """Delete a business card."""
    card = get_object_or_404(BusinessCard, id=card_id)
    if not can_access_card(request.user, card, require_edit=True):
        messages.error(request, "You don't have permission to delete this card.")
        return redirect('user_dashboard')

    if request.method == 'POST':
        card_name = card.full_name
        card.delete()
        messages.success(request, f'Business card "{card_name}" deleted successfully!')
        return redirect('user_dashboard')

    return render(request, 'auth/delete_card.html', {'card': card})


@login_required
def billing(request):
    """
    Billing & plan page.
    Shows current plan, usage, and a simulated invoice history.
    No real payment data — invoices are generated from the org's creation date.
    """
    org = get_user_org(request.user)

    # Build simulated invoice history (one per month since plan was activated,
    # up to a max of 12 entries). Free plan → no invoices.
    invoices = []
    if org and org.plan != Plan.FREE:
        price_cents = 900 if org.plan == Plan.PRO else 2900
        price_str   = '$9.00' if org.plan == Plan.PRO else '$29.00'
        label       = PLAN_LABELS[org.plan]
        # Start from the org's creation month
        start = org.created_at.date().replace(day=1)
        today = date.today()
        cursor = start
        while cursor <= today and len(invoices) < 12:
            invoices.append({
                'date':        cursor,
                'description': f'VCard Manager {label} — Monthly',
                'amount':      price_str,
                'status':      'Paid',
                'invoice_id':  f'INV-SIM-{cursor.strftime("%Y%m")}-{price_cents}',
            })
            cursor += relativedelta(months=1)
        invoices.reverse()  # most recent first

    context = {
        'org':       org,
        'invoices':  invoices,
        'plan':      org.plan if org else Plan.FREE,
        'has_paid_plan': org and org.plan != Plan.FREE,
    }
    return render(request, 'auth/billing.html', context)


@require_POST
def submit_lead(request, url_slug):
    """Handle contact form submission from a public card page."""
    card = get_object_or_404(BusinessCard, custom_url=url_slug, is_active=True)

    name    = request.POST.get('name', '').strip()
    email   = request.POST.get('email', '').strip()
    phone   = request.POST.get('phone', '').strip()
    message = request.POST.get('message', '').strip()

    errors = []
    if not name:
        errors.append('Name is required.')
    if not email or '@' not in email:
        errors.append('A valid email is required.')
    if not message:
        errors.append('Message is required.')
    if len(message) > 1000:
        errors.append('Message must be under 1000 characters.')

    if errors:
        messages.error(request, ' '.join(errors))
        return redirect(card.get_absolute_url() + '#contact')

    CardLead.objects.create(
        card=card,
        name=name,
        email=email,
        phone=phone,
        message=message,
        ip_address=get_client_ip(request),
    )
    messages.success(request, 'Your message was sent! We\'ll be in touch soon.')
    return redirect(card.get_absolute_url() + '#contact')


@login_required
def leads_inbox(request):
    """Show all leads for cards owned by the user's org."""
    org = get_user_org(request.user)
    if not org:
        return redirect('user_dashboard')

    card_filter = request.GET.get('card', '')
    read_filter = request.GET.get('read', '')

    org_card_ids = org.business_cards.values_list('id', flat=True)
    leads_qs = CardLead.objects.filter(card_id__in=org_card_ids).select_related('card')

    if card_filter:
        leads_qs = leads_qs.filter(card_id=card_filter)
    if read_filter == 'unread':
        leads_qs = leads_qs.filter(is_read=False)
    elif read_filter == 'read':
        leads_qs = leads_qs.filter(is_read=True)

    # Mark as read if ?mark_read=<id>
    mark_id = request.GET.get('mark_read')
    if mark_id:
        CardLead.objects.filter(id=mark_id, card_id__in=org_card_ids).update(is_read=True)
        return redirect(request.path + ('?' + request.GET.urlencode().replace(f'mark_read={mark_id}', '').strip('&') if request.GET else ''))

    user_cards = org.business_cards.all()
    unread_count = CardLead.objects.filter(card_id__in=org_card_ids, is_read=False).count()

    return render(request, 'auth/leads_inbox.html', {
        'leads':        leads_qs,
        'user_cards':   user_cards,
        'card_filter':  card_filter,
        'read_filter':  read_filter,
        'unread_count': unread_count,
        'org':          org,
    })


# ── Team Management ────────────────────────────────────────────────────────────

@login_required
def team_management(request):
    """
    Team management page — list members, pending invites, invite new members.
    Restricted to Business plan. Only owner/admin may manage members.
    """
    org = get_user_org(request.user)
    if not org:
        return redirect('user_dashboard')

    member = org.get_member(request.user)

    # Business-plan gate
    if org.plan != Plan.BUSINESS:
        messages.warning(request, 'Team management is available on the Business plan.')
        return redirect('upgrade_plan')

    # Permission gate
    if not member or not member.can_manage_members:
        messages.error(request, "You don't have permission to manage team members.")
        return redirect('user_dashboard')

    accepted_members = org.members.filter(invite_accepted=True).select_related('user').order_by('role', 'joined_at')
    pending_invites  = org.members.filter(invite_accepted=False).order_by('joined_at')

    # Build the full invite link for each pending invite (for display)
    from django.urls import reverse
    pending_with_links = []
    for inv in pending_invites:
        link = request.build_absolute_uri(reverse('accept_invite', args=[inv.invite_token]))
        pending_with_links.append({'member': inv, 'link': link})

    context = {
        'org':             org,
        'member':          member,
        'accepted_members': accepted_members,
        'pending_invites':  pending_with_links,
        'seat_count':      org.seat_count,
        'seat_limit':      org.seat_limit,
        'can_add_member':  org.can_add_member,
        'roles':           OrganizationMember.Role.choices,
    }
    return render(request, 'auth/team.html', context)


@login_required
@require_POST
def invite_member(request):
    """Send (simulate) a team invite. Creates a pending OrganizationMember."""
    org = get_user_org(request.user)
    if not org or org.plan != Plan.BUSINESS:
        messages.error(request, 'Team invites require the Business plan.')
        return redirect('upgrade_plan')

    member = org.get_member(request.user)
    if not member or not member.can_manage_members:
        messages.error(request, "You don't have permission to invite members.")
        return redirect('team_management')

    if not org.can_add_member:
        messages.error(request, f'Seat limit reached ({org.seat_limit}). Upgrade or remove a member first.')
        return redirect('team_management')

    email = request.POST.get('email', '').strip().lower()
    role  = request.POST.get('role', OrganizationMember.Role.VIEWER)

    if not email or '@' not in email:
        messages.error(request, 'Please enter a valid email address.')
        return redirect('team_management')

    if role not in dict(OrganizationMember.Role.choices):
        role = OrganizationMember.Role.VIEWER

    # Prevent duplicate invites / existing members
    if org.members.filter(invited_email=email).exists():
        messages.warning(request, f'{email} has already been invited or is already a member.')
        return redirect('team_management')

    # Also check if there's already a user with that email in this org
    from django.contrib.auth import get_user_model
    User = get_user_model()
    existing_user = User.objects.filter(email=email).first()
    if existing_user and org.has_member(existing_user):
        messages.warning(request, f'{email} is already a member of this workspace.')
        return redirect('team_management')

    OrganizationMember.objects.create(
        organization=org,
        user=existing_user,          # link immediately if user exists; else None
        role=role,
        invited_email=email,
        invite_token=__import__('uuid').uuid4(),
        invite_accepted=False,
    )

    messages.success(request, f'Invite sent to {email}. Share the invite link with them.')
    return redirect('team_management')


@login_required
@require_POST
def remove_member(request, member_id):
    """Remove a member (or revoke a pending invite)."""
    org = get_user_org(request.user)
    if not org:
        return redirect('user_dashboard')

    actor = org.get_member(request.user)
    if not actor or not actor.can_manage_members:
        messages.error(request, "You don't have permission to remove members.")
        return redirect('team_management')

    target = get_object_or_404(OrganizationMember, id=member_id, organization=org)

    if target.role == OrganizationMember.Role.OWNER:
        messages.error(request, "Cannot remove the workspace owner.")
        return redirect('team_management')

    # Can't remove yourself if you're the only admin
    if target.user == request.user:
        messages.error(request, "You can't remove yourself. Transfer ownership first.")
        return redirect('team_management')

    name = target.user.get_full_name() if target.user else target.invited_email
    target.delete()
    messages.success(request, f'{name} has been removed from the workspace.')
    return redirect('team_management')


@login_required
@require_POST
def change_member_role(request, member_id):
    """Change the role of an existing member."""
    org = get_user_org(request.user)
    if not org:
        return redirect('user_dashboard')

    actor = org.get_member(request.user)
    if not actor or not actor.can_manage_members:
        messages.error(request, "You don't have permission to change roles.")
        return redirect('team_management')

    target = get_object_or_404(OrganizationMember, id=member_id, organization=org)
    new_role = request.POST.get('role', '')

    if target.role == OrganizationMember.Role.OWNER:
        messages.error(request, "Cannot change the owner's role.")
        return redirect('team_management')

    if new_role not in dict(OrganizationMember.Role.choices):
        messages.error(request, 'Invalid role.')
        return redirect('team_management')

    target.role = new_role
    target.save(update_fields=['role'])
    name = target.user.get_full_name() if target.user else target.invited_email
    messages.success(request, f"{name}'s role updated to {new_role.title()}.")
    return redirect('team_management')


def accept_invite(request, token):
    """
    Public invite-acceptance page.
    If the user is logged in → accept immediately.
    If not → show login/register prompt, then accept after auth.
    """
    invite = get_object_or_404(OrganizationMember, invite_token=token, invite_accepted=False)

    if request.method == 'POST' and request.user.is_authenticated:
        # Guard: email must match the invite
        if invite.invited_email and request.user.email.lower() != invite.invited_email.lower():
            messages.error(
                request,
                f'This invite was sent to {invite.invited_email}. '
                f'Please sign in with that email address, or ask to be re-invited.'
            )
            return render(request, 'auth/accept_invite.html', {'invite': invite, 'org': invite.organization})

        # Guard: already a member?
        if invite.organization.has_member(request.user):
            messages.info(request, 'You are already a member of this workspace.')
            return redirect('user_dashboard')

        invite.user           = request.user
        invite.invite_accepted = True
        invite.save(update_fields=['user', 'invite_accepted'])
        messages.success(request, f'Welcome to {invite.organization.name}!')
        return redirect('user_dashboard')

    return render(request, 'auth/accept_invite.html', {
        'invite': invite,
        'org':    invite.organization,
    })
