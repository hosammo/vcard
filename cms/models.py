import datetime
from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.search import index
from wagtail.blocks import RichTextBlock, CharBlock
from wagtail.images.blocks import ImageChooserBlock
from .blocks import FeatureBlock, StepBlock, TestimonialBlock, PricingTierBlock, FAQBlock


class HomePage(Page):
    hero_badge_text = models.CharField(max_length=200, blank=True)
    hero_heading = models.CharField(max_length=300, default='Your digital identity, one tap away')
    hero_subtext = models.TextField(blank=True)
    hero_primary_cta_label = models.CharField(max_length=100, default="Create your card — it's free")
    hero_secondary_cta_label = models.CharField(max_length=100, default='See how it works →')
    hero_social_proof_text = models.CharField(max_length=200, blank=True, default='12,000+ professionals already use VCard')

    features = StreamField([('feature', FeatureBlock())], blank=True, use_json_field=True)
    steps = StreamField([('step', StepBlock())], blank=True, use_json_field=True)
    testimonials = StreamField([('testimonial', TestimonialBlock())], blank=True, use_json_field=True)

    cta_heading = models.CharField(max_length=200, blank=True, default='Ready to make your mark?')
    cta_subtext = models.CharField(max_length=300, blank=True, default="Join 12,000+ professionals who've gone digital. Free to start, no credit card required.")
    cta_button_label = models.CharField(max_length=100, default='Start your free card →')

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel('hero_badge_text'),
            FieldPanel('hero_heading'),
            FieldPanel('hero_subtext'),
            FieldPanel('hero_primary_cta_label'),
            FieldPanel('hero_secondary_cta_label'),
            FieldPanel('hero_social_proof_text'),
        ], heading='Hero Section'),
        FieldPanel('features'),
        FieldPanel('steps'),
        FieldPanel('testimonials'),
        MultiFieldPanel([
            FieldPanel('cta_heading'),
            FieldPanel('cta_subtext'),
            FieldPanel('cta_button_label'),
        ], heading='CTA Banner'),
    ]

    subpage_types = ['cms.BlogIndexPage', 'cms.AboutPage', 'cms.PricingPage', 'cms.LegalPage']

    class Meta:
        verbose_name = 'Home Page'


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('intro'),
    ]

    parent_page_types = ['cms.HomePage']
    subpage_types = ['cms.BlogPostPage']

    def get_context(self, request):
        context = super().get_context(request)
        from django.core.paginator import Paginator
        posts = BlogPostPage.objects.child_of(self).live().order_by('-published_date')
        paginator = Paginator(posts, 10)
        context['posts'] = paginator.get_page(request.GET.get('page', 1))
        return context

    class Meta:
        verbose_name = 'Blog'


class BlogPostPage(Page):
    author = models.CharField(max_length=200)
    published_date = models.DateField(default=datetime.date.today)
    hero_image = models.ForeignKey(
        'wagtailimages.Image', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='+',
    )
    excerpt = models.TextField(blank=True, max_length=500)
    body = StreamField([
        ('paragraph', RichTextBlock()),
        ('heading', CharBlock(form_classname='title')),
        ('image', ImageChooserBlock()),
    ], use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel('author'),
        FieldPanel('published_date'),
        FieldPanel('hero_image'),
        FieldPanel('excerpt'),
        FieldPanel('body'),
    ]

    search_fields = Page.search_fields + [
        index.SearchField('body'),
        index.SearchField('excerpt'),
    ]

    parent_page_types = ['cms.BlogIndexPage']
    subpage_types = []

    class Meta:
        verbose_name = 'Blog Post'


class AboutPage(Page):
    body = StreamField([
        ('paragraph', RichTextBlock()),
        ('heading', CharBlock()),
        ('image', ImageChooserBlock()),
    ], use_json_field=True, blank=True)

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]

    parent_page_types = ['cms.HomePage']
    subpage_types = []

    class Meta:
        verbose_name = 'About Page'


class PricingPage(Page):
    heading = models.CharField(max_length=200, default='Simple, transparent pricing')
    subtext = models.CharField(max_length=400, blank=True, default="Start free. Upgrade when you're ready.")
    tiers = StreamField([('tier', PricingTierBlock())], blank=True, use_json_field=True)
    faq = StreamField([('faq', FAQBlock())], blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel('heading'),
        FieldPanel('subtext'),
        FieldPanel('tiers'),
        FieldPanel('faq'),
    ]

    parent_page_types = ['cms.HomePage']
    subpage_types = []

    class Meta:
        verbose_name = 'Pricing Page'


class LegalPage(Page):
    body = RichTextField()

    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]

    parent_page_types = ['cms.HomePage']
    subpage_types = []

    class Meta:
        verbose_name = 'Legal Page'
