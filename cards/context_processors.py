from .models import OrganizationMember, CardLead


def org_context(request):
    """
    Inject the current user's primary Organization and their membership
    into every template context automatically.
    """
    if not request.user.is_authenticated:
        return {}

    membership = (
        request.user.org_memberships
        .filter(invite_accepted=True)
        .select_related('organization')
        .order_by('joined_at')
        .first()
    )

    # Prefer the membership where the user is owner
    owner_membership = (
        request.user.org_memberships
        .filter(invite_accepted=True, role=OrganizationMember.Role.OWNER)
        .select_related('organization')
        .first()
    )
    active = owner_membership or membership

    if not active:
        return {}

    org    = active.organization
    member = active

    org_card_ids = org.business_cards.values_list('id', flat=True)
    unread_leads = CardLead.objects.filter(card_id__in=org_card_ids, is_read=False).count()

    return {
        'current_org':          org,
        'current_member':       member,
        'current_plan':         org.plan,
        'can_add_card':         org.can_add_card,
        'has_analytics':        org.has_analytics,
        'has_csv_export':       org.has_csv_export,
        'current_unread_leads': unread_leads or None,
    }
