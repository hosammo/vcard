"""
Data migration — Phase 1A backfill
===================================
For every existing User:
  1. Create a personal Free Organization  (<name>'s Workspace)
  2. Add them as the Owner member
  3. Assign all BusinessCards owned by that user to the new org
"""

from django.db import migrations
import uuid


def forwards(apps, schema_editor):
    User         = apps.get_model('auth', 'User')
    Organization = apps.get_model('cards', 'Organization')
    OrgMember    = apps.get_model('cards', 'OrganizationMember')
    BusinessCard = apps.get_model('cards', 'BusinessCard')

    def unique_slug(base):
        from django.utils.text import slugify
        slug = slugify(base) or 'workspace'
        candidate = slug
        n = 1
        while Organization.objects.filter(slug=candidate).exists():
            candidate = f"{slug}-{n}"
            n += 1
        return candidate

    for user in User.objects.all():
        # Skip if the user already has an org (shouldn't happen, but be safe)
        if OrgMember.objects.filter(user=user, invite_accepted=True).exists():
            existing_org = OrgMember.objects.filter(
                user=user, invite_accepted=True
            ).first().organization
            # Still link any un-linked cards
            BusinessCard.objects.filter(owner=user, organization__isnull=True).update(
                organization=existing_org
            )
            continue

        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        org = Organization.objects.create(
            id=uuid.uuid4(),
            name=f"{full_name}'s Workspace",
            slug=unique_slug(user.username),
            plan='free',
            is_active=True,
        )

        OrgMember.objects.create(
            organization=org,
            user=user,
            role='owner',
            invited_email=user.email or '',
            invite_token=uuid.uuid4(),
            invite_accepted=True,
        )

        # Assign all cards that belong to this user
        BusinessCard.objects.filter(owner=user, organization__isnull=True).update(
            organization=org
        )


def backwards(apps, schema_editor):
    """Reverse: unlink cards and remove organizations created by this migration."""
    Organization = apps.get_model('cards', 'Organization')
    BusinessCard = apps.get_model('cards', 'BusinessCard')
    # Detach cards from orgs
    BusinessCard.objects.all().update(organization=None)
    # Remove all orgs (members cascade-delete)
    Organization.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('cards', '0007_add_organization_models'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
