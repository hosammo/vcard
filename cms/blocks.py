from wagtail.blocks import (
    CharBlock, TextBlock, RichTextBlock, StructBlock, ListBlock, BooleanBlock,
)
from wagtail.images.blocks import ImageChooserBlock


class FeatureBlock(StructBlock):
    icon = CharBlock(max_length=10, help_text='Emoji or single character icon')
    title = CharBlock(max_length=100)
    description = TextBlock()

    class Meta:
        icon = 'placeholder'
        label = 'Feature'


class StepBlock(StructBlock):
    title = CharBlock(max_length=100)
    description = TextBlock()

    class Meta:
        icon = 'order'
        label = 'Step'


class TestimonialBlock(StructBlock):
    quote = TextBlock()
    author_name = CharBlock(max_length=100)
    author_role = CharBlock(max_length=100)
    avatar = ImageChooserBlock(required=False)

    class Meta:
        icon = 'user'
        label = 'Testimonial'


class PricingTierBlock(StructBlock):
    name = CharBlock(max_length=50)
    price = CharBlock(max_length=20, help_text='e.g. $9.99')
    period = CharBlock(max_length=20, default='/mo')
    description = CharBlock(max_length=200)
    features = ListBlock(CharBlock(max_length=200))
    is_popular = BooleanBlock(required=False, default=False)
    cta_label = CharBlock(max_length=50)
    cta_url = CharBlock(max_length=200)

    class Meta:
        icon = 'pick'
        label = 'Pricing Tier'


class FAQBlock(StructBlock):
    question = CharBlock(max_length=300)
    answer = RichTextBlock()

    class Meta:
        icon = 'help'
        label = 'FAQ Item'
