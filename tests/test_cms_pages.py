from django.test import TestCase
from cms.blocks import FeatureBlock, StepBlock, TestimonialBlock, PricingTierBlock, FAQBlock


class BlockImportTest(TestCase):
    def test_all_blocks_importable(self):
        self.assertIsNotNone(FeatureBlock)
        self.assertIsNotNone(StepBlock)
        self.assertIsNotNone(TestimonialBlock)
        self.assertIsNotNone(PricingTierBlock)
        self.assertIsNotNone(FAQBlock)


from wagtail.test.utils import WagtailPageTests
from wagtail.models import Page
from cms.models import (
    HomePage, BlogIndexPage, BlogPostPage, AboutPage, PricingPage, LegalPage
)


class HomePageTests(WagtailPageTests):
    def test_can_create_under_root(self):
        self.assertCanCreateAt(Page, HomePage)

    def test_can_create_blog_index_under_home(self):
        self.assertCanCreateAt(HomePage, BlogIndexPage)

    def test_can_create_about_under_home(self):
        self.assertCanCreateAt(HomePage, AboutPage)

    def test_can_create_pricing_under_home(self):
        self.assertCanCreateAt(HomePage, PricingPage)

    def test_can_create_legal_under_home(self):
        self.assertCanCreateAt(HomePage, LegalPage)

    def test_blog_post_only_under_blog_index(self):
        self.assertCanCreateAt(BlogIndexPage, BlogPostPage)
        self.assertCanNotCreateAt(HomePage, BlogPostPage)
