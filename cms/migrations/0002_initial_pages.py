from django.db import migrations


def create_page_tree(apps, schema_editor):
    from wagtail.models import Page, Site
    from cms.models import HomePage, BlogIndexPage, AboutPage, PricingPage, LegalPage

    if HomePage.objects.exists():
        return

    root = Page.objects.get(depth=1)

    # Rename any existing depth-2 page occupying our 'home' slug
    db = schema_editor.connection
    with db.cursor() as cur:
        cur.execute(
            "UPDATE wagtailcore_page SET slug='wagtail-welcome' WHERE depth=2 AND slug='home'"
        )

    home = HomePage(
        title='VCard — Digital Business Cards',
        slug='home',
        hero_heading='Your digital identity, one tap away',
        hero_badge_text='✦ NFC-ready digital business cards',
        hero_subtext='Create a stunning digital business card in minutes. Share via NFC, QR code, or link. Track every interaction with real-time analytics.',
        cta_heading='Ready to make your mark?',
        cta_subtext="Join 12,000+ professionals who've gone digital. Free to start, no credit card required.",
        cta_button_label='Start your free card →',
        show_in_menus=True,
    )
    root.add_child(instance=home)

    site, created = Site.objects.get_or_create(
        hostname='localhost',
        defaults={'root_page': home, 'site_name': 'VCard', 'is_default_site': True, 'port': 80},
    )
    if not created:
        site.root_page = home
        site.site_name = 'VCard'
        site.is_default_site = True
        site.save()

    blog = BlogIndexPage(title='Blog', slug='blog', show_in_menus=True)
    home.add_child(instance=blog)

    about = AboutPage(title='About', slug='about', show_in_menus=True)
    home.add_child(instance=about)

    pricing = PricingPage(
        title='Pricing', slug='pricing',
        heading='Simple, transparent pricing',
        subtext="Start free. Upgrade when you're ready.",
        show_in_menus=True,
    )
    home.add_child(instance=pricing)

    privacy = LegalPage(title='Privacy Policy', slug='privacy', body='<p>Privacy policy content coming soon.</p>')
    home.add_child(instance=privacy)

    terms = LegalPage(title='Terms of Service', slug='terms', body='<p>Terms of service content coming soon.</p>')
    home.add_child(instance=terms)


def delete_page_tree(apps, schema_editor):
    from wagtail.models import Page
    Page.objects.filter(depth__gte=2).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('cms', '0001_initial'),
        ('wagtailcore', '0094_alter_page_locale'),
        ('wagtailsearch', '0008_remove_query_and_querydailyhits_models'),
        ('wagtailredirects', '0008_add_verbose_name_plural'),
    ]

    operations = [
        migrations.RunPython(create_page_tree, delete_page_tree),
    ]
