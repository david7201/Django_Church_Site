import secrets
import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone

from .utils import optimize_image_field


LANGUAGE_ENGLISH = "en"
LANGUAGE_ROMANIAN = "ro"
LANGUAGE_CHOICES = [
    (LANGUAGE_ENGLISH, "English"),
    (LANGUAGE_ROMANIAN, "Romanian"),
]

STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_ARCHIVED = "archived"
STATUS_CHOICES = [
    (STATUS_DRAFT, "Draft"),
    (STATUS_PUBLISHED, "Published"),
    (STATUS_ARCHIVED, "Archived"),
]

VISIBILITY_PUBLIC = "public"
VISIBILITY_MEMBERS = "members"
VISIBILITY_CHOICES = [
    (VISIBILITY_PUBLIC, "Everyone"),
    (VISIBILITY_MEMBERS, "Logged-in users only"),
]

NEWSLETTER_CATEGORIES = [
    ("general", "General"),
    ("fundraising", "Fundraising"),
    ("youth", "Youth"),
    ("prayer", "Prayer"),
    ("services", "Services"),
    ("building", "Building Updates"),
]


def default_invite_expiry():
    return timezone.now() + timedelta(days=7)


def generate_secure_token():
    return secrets.token_urlsafe(32)


class AuditModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_%(class)s_set",
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_%(class)s_set",
        editable=False,
    )

    class Meta:
        abstract = True


class PublishableQuerySet(models.QuerySet):
    def live(self):
        now = timezone.now()
        return (
            self.filter(is_visible=True, status=STATUS_PUBLISHED)
            .filter(Q(publish_at__isnull=True) | Q(publish_at__lte=now))
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gte=now))
        )

    def visible_to(self, user):
        queryset = self.live()
        if not getattr(user, "is_authenticated", False):
            queryset = queryset.filter(visibility=VISIBILITY_PUBLIC)
        return queryset


class PublishableModel(AuditModel):
    is_visible = models.BooleanField(
        "Show on website",
        default=True,
        help_text="Turn this off to hide it without deleting it.",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_PUBLIC)
    publish_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    objects = PublishableQuerySet.as_manager()

    class Meta:
        abstract = True

    @property
    def is_live(self):
        now = timezone.now()
        return (
            self.is_visible
            and self.status == STATUS_PUBLISHED
            and (self.publish_at is None or self.publish_at <= now)
            and (self.expires_at is None or self.expires_at >= now)
        )


class ImageAsset(AuditModel):
    CATEGORY_GENERAL = "general"
    CATEGORY_HERO = "hero"
    CATEGORY_EVENT = "event"
    CATEGORY_BUILDING = "building"
    CATEGORY_DONATION = "donation"
    CATEGORY_TEAM = "team"

    CATEGORY_CHOICES = [
        (CATEGORY_GENERAL, "General"),
        (CATEGORY_HERO, "Hero images"),
        (CATEGORY_EVENT, "Events"),
        (CATEGORY_BUILDING, "Building project"),
        (CATEGORY_DONATION, "Donation images and QR codes"),
        (CATEGORY_TEAM, "Team"),
    ]

    title = models.CharField(max_length=160)
    image = models.ImageField(upload_to="gallery/%Y/%m/")
    alt_text_en = models.CharField("Alt text in English", max_length=200, blank=True)
    alt_text_ro = models.CharField("Alt text in Romanian", max_length=200, blank=True)
    caption_en = models.CharField("Caption in English", max_length=255, blank=True)
    caption_ro = models.CharField("Caption in Romanian", max_length=255, blank=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default=CATEGORY_GENERAL)

    class Meta:
        ordering = ["title"]
        verbose_name = "Reusable image"
        verbose_name_plural = "Reusable images"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.image:
            optimize_image_field(self.image)
        super().save(*args, **kwargs)


class SiteSettings(AuditModel):
    church_name = models.CharField(max_length=160, default="Mount Zion")
    tagline_en = models.CharField(max_length=200, default="Romanian Pentecostal Church")
    tagline_ro = models.CharField(max_length=200, blank=True)
    default_meta_title_en = models.CharField(max_length=180, default="Mount Zion Church")
    default_meta_title_ro = models.CharField(max_length=180, blank=True)
    default_meta_description_en = models.TextField(
        default="Mount Zion is a Romanian Pentecostal church in Dunshaughlin, Ireland."
    )
    default_meta_description_ro = models.TextField(blank=True)
    logo = models.ForeignKey(
        ImageAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="logo_settings",
    )
    hero_image = models.ForeignKey(
        ImageAsset,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hero_settings",
    )
    hero_image_static = models.CharField(
        max_length=255,
        blank=True,
        default="logo/mt2.jpeg",
        help_text="Fallback static image path, for example logo/mt2.jpeg.",
    )
    scripture_reference_en = models.CharField(max_length=80, default="Micah 4:5")
    scripture_reference_ro = models.CharField(max_length=80, blank=True, default="Mica 4:5")
    scripture_text_en = models.TextField(
        default=(
            "For all people will walk every one in the name of his god, and we will walk "
            "in the name of the Lord our God for ever and ever."
        )
    )
    scripture_text_ro = models.TextField(
        blank=True,
        default=(
            "„Pe când toate popoarele umblă fiecare în numele dumnezeului său, noi vom umbla "
            "în Numele Domnului, Dumnezeului nostru, totdeauna şi în veci de veci!”"
        ),
    )
    footer_text_en = models.CharField(max_length=180, default="Copyright Mount Zion Church")
    footer_text_ro = models.CharField(max_length=180, blank=True)
    address = models.TextField(default='THE ROMANIAN PENTECOSTAL CHURCH "MOUNT ZION"\nGROWTOWN DUNSHAUGHLIN\nCO. MEATH\nA85 WY11')
    email = models.EmailField(default="mountziondublin@gmail.com")
    phone = models.CharField(max_length=40, default="+353 089 452 4148")
    directions_url = models.URLField(
        blank=True,
        default="https://www.google.com/maps/dir/?api=1&destination=GROWTOWN+DUNSHAUGHLIN%2C+A85+WY11",
    )
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    show_home_scripture = models.BooleanField("Homepage scripture", default=True)
    show_home_service_schedule = models.BooleanField("Homepage service schedule", default=True)
    show_home_fundraising = models.BooleanField("Homepage fundraising progress", default=True)
    show_home_latest_update = models.BooleanField("Homepage latest building update", default=True)
    show_home_team = models.BooleanField("Homepage team section", default=True)
    show_home_newsletter = models.BooleanField("Homepage newsletter signup", default=True)
    show_home_contact_details = models.BooleanField("Homepage contact details", default=True)
    show_charity_donations = models.BooleanField("Charity donation section", default=True)
    show_building_fundraising = models.BooleanField("Building fundraising progress", default=True)
    show_building_giving_tiers = models.BooleanField("Building giving tiers", default=True)
    show_building_milestones = models.BooleanField("Building construction timeline", default=True)
    show_building_updates = models.BooleanField("Building photo updates", default=True)
    show_events_listing = models.BooleanField("Events listing", default=True)
    show_contact_details = models.BooleanField("Contact page details", default=True)
    show_contact_forms = models.BooleanField("Contact and prayer forms", default=True)
    show_footer = models.BooleanField("Website footer", default=True)
    show_construction_popup = models.BooleanField(default=True)
    construction_popup_title_en = models.CharField(max_length=120, default="Church Building Update")
    construction_popup_title_ro = models.CharField(max_length=120, blank=True)
    construction_popup_body_en = models.TextField(
        default="Our church is currently under construction. Services are being held at a different location."
    )
    construction_popup_body_ro = models.TextField(blank=True)
    construction_popup_button_en = models.CharField(max_length=80, default="Go to Current Church")
    construction_popup_button_ro = models.CharField(max_length=80, blank=True)
    current_church_url = models.URLField(blank=True, default="https://maps.app.goo.gl/1Qcd51AxkUctyZXP8")

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return self.church_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Page(AuditModel):
    slug = models.SlugField(unique=True)
    nav_title_en = models.CharField(max_length=80)
    nav_title_ro = models.CharField(max_length=80, blank=True)
    meta_title_en = models.CharField(max_length=180, blank=True)
    meta_title_ro = models.CharField(max_length=180, blank=True)
    meta_description_en = models.TextField(blank=True)
    meta_description_ro = models.TextField(blank=True)
    hero_title_en = models.CharField(max_length=160)
    hero_title_ro = models.CharField(max_length=160, blank=True)
    hero_subtitle_en = models.CharField(max_length=255, blank=True)
    hero_subtitle_ro = models.CharField(max_length=255, blank=True)
    hero_button_text_en = models.CharField(max_length=80, blank=True)
    hero_button_text_ro = models.CharField(max_length=80, blank=True)
    hero_button_url = models.CharField(max_length=255, blank=True)
    hero_image = models.ForeignKey(ImageAsset, on_delete=models.SET_NULL, null=True, blank=True)
    hero_image_static = models.CharField(max_length=255, blank=True)
    body_id = models.CharField(max_length=80, blank=True, default="page-top")
    is_visible = models.BooleanField(
        "Show on website",
        default=True,
        help_text="Turn this off to hide the entire page without deleting it.",
    )
    show_hero = models.BooleanField(default=True)
    show_in_navigation = models.BooleanField(default=True)
    navigation_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["navigation_order", "nav_title_en"]

    def __str__(self):
        return self.nav_title_en

    def get_absolute_url(self):
        route_names = {
            "home": "home",
            "about": "about",
            "services": "services",
            "charity": "charity",
            "building": "building_fund",
            "events": "events",
            "contact": "contact",
            "member-updates": "member_updates",
        }
        route_name = route_names.get(self.slug)
        if route_name:
            return reverse(route_name)
        return reverse("page", kwargs={"slug": self.slug})


class PageBlock(AuditModel):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="blocks")
    key = models.SlugField()
    label = models.CharField(max_length=120)
    title_en = models.CharField(max_length=180, blank=True)
    title_ro = models.CharField(max_length=180, blank=True)
    subtitle_en = models.CharField(max_length=180, blank=True)
    subtitle_ro = models.CharField(max_length=180, blank=True)
    body_en = models.TextField(blank=True)
    body_ro = models.TextField(blank=True)
    image = models.ForeignKey(ImageAsset, on_delete=models.SET_NULL, null=True, blank=True)
    image_static = models.CharField(max_length=255, blank=True)
    button_text_en = models.CharField(max_length=80, blank=True)
    button_text_ro = models.CharField(max_length=80, blank=True)
    button_url = models.CharField(max_length=255, blank=True)
    is_visible = models.BooleanField(
        "Show on website",
        default=True,
        help_text="Turn this off to hide this built-in page section without deleting it.",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["page", "order", "label"]
        unique_together = ("page", "key")
        verbose_name = "Built-in page section"
        verbose_name_plural = "Built-in page sections"

    def __str__(self):
        return f"{self.page}: {self.label}"


class PageSection(PublishableModel):
    LAYOUT_TEXT_CARD = "text_card"
    LAYOUT_VALUE_CARD = "value_card"
    LAYOUT_IMAGE_TEXT = "image_text"
    LAYOUT_DARK_BAND = "dark_band"
    LAYOUT_CHOICES = [
        (LAYOUT_TEXT_CARD, "Text card"),
        (LAYOUT_VALUE_CARD, "Value card"),
        (LAYOUT_IMAGE_TEXT, "Image and text row"),
        (LAYOUT_DARK_BAND, "Dark full-width band"),
    ]

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="sections")
    title_en = models.CharField(max_length=180)
    title_ro = models.CharField(max_length=180, blank=True)
    body_en = models.TextField(blank=True)
    body_ro = models.TextField(blank=True)
    image = models.ForeignKey(ImageAsset, on_delete=models.SET_NULL, null=True, blank=True)
    image_static = models.CharField(max_length=255, blank=True)
    button_text_en = models.CharField(max_length=80, blank=True)
    button_text_ro = models.CharField(max_length=80, blank=True)
    button_url = models.CharField(max_length=255, blank=True)
    layout = models.CharField(max_length=30, choices=LAYOUT_CHOICES, default=LAYOUT_TEXT_CARD)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["page", "order", "title_en"]

    def __str__(self):
        return f"{self.page}: {self.title_en}"


class ServiceTime(AuditModel):
    day_order = models.PositiveIntegerField(default=0)
    day_en = models.CharField(max_length=40)
    day_ro = models.CharField(max_length=40, blank=True)
    service_name_en = models.CharField(max_length=120, blank=True)
    service_name_ro = models.CharField(max_length=120, blank=True)
    time_text = models.CharField(max_length=120, blank=True)
    is_closed = models.BooleanField(default=False)
    is_visible = models.BooleanField(
        "Show on website",
        default=True,
        help_text="Turn this off to hide this service time without deleting it.",
    )

    class Meta:
        ordering = ["day_order"]

    def __str__(self):
        return self.day_en


class TeamMember(PublishableModel):
    name = models.CharField(max_length=120)
    role_en = models.CharField(max_length=120)
    role_ro = models.CharField(max_length=120, blank=True)
    bio_en = models.TextField(blank=True)
    bio_ro = models.TextField(blank=True)
    photo = models.ForeignKey(ImageAsset, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class Announcement(PublishableModel):
    category = models.CharField(max_length=30, choices=NEWSLETTER_CATEGORIES, default="general")
    title_en = models.CharField(max_length=180)
    title_ro = models.CharField(max_length=180, blank=True)
    body_en = models.TextField(blank=True)
    body_ro = models.TextField(blank=True)
    is_urgent = models.BooleanField(default=False)
    link_text_en = models.CharField(max_length=80, blank=True)
    link_text_ro = models.CharField(max_length=80, blank=True)
    link_url = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-is_urgent", "-publish_at", "-created_at"]

    def __str__(self):
        return self.title_en


class Event(PublishableModel):
    title_en = models.CharField(max_length=180)
    title_ro = models.CharField(max_length=180, blank=True)
    slug = models.SlugField(unique=True)
    event_date = models.DateField(null=True, blank=True)
    location_en = models.CharField(max_length=180, blank=True)
    location_ro = models.CharField(max_length=180, blank=True)
    summary_en = models.TextField(blank=True)
    summary_ro = models.TextField(blank=True)
    body_en = models.TextField(blank=True)
    body_ro = models.TextField(blank=True)
    show_hero = models.BooleanField("Show event hero", default=True)
    show_description = models.BooleanField("Show event description", default=True)
    show_gallery = models.BooleanField("Show event slideshow", default=True)
    featured = models.BooleanField(default=False)
    cover_image = models.ForeignKey(ImageAsset, on_delete=models.SET_NULL, null=True, blank=True)
    cover_image_static = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-event_date", "-publish_at", "-created_at"]

    def __str__(self):
        return self.title_en

    def get_absolute_url(self):
        return reverse("event_detail", kwargs={"slug": self.slug})


class EventImage(AuditModel):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="images")
    image = models.ForeignKey(ImageAsset, on_delete=models.CASCADE)
    caption_en = models.CharField(max_length=180, blank=True)
    caption_ro = models.CharField(max_length=180, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(
        "Show in slideshow",
        default=True,
        help_text="Turn this off to hide this photo without removing it from the event.",
    )

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.event}: {self.image}"


class FundraisingCampaign(PublishableModel):
    title_en = models.CharField(max_length=180, default="New Church Building Fund")
    title_ro = models.CharField(max_length=180, blank=True)
    description_en = models.TextField(blank=True)
    description_ro = models.TextField(blank=True)
    goal_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    raised_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    current_milestone_step = models.PositiveSmallIntegerField(
        default=0,
        help_text=(
            "Set 0 before construction starts, 1 for the first milestone, 2 for the second, "
            "and so on. The public construction progress updates automatically."
        ),
    )
    is_primary = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_primary", "-created_at"]

    def __str__(self):
        return self.title_en

    @property
    def progress_percent(self):
        if not self.goal_amount:
            return 0
        percent = (self.raised_amount / self.goal_amount) * Decimal("100")
        return min(100, int(percent))

    def sync_milestone_statuses(self):
        milestones = list(self.milestones.order_by("order", "target_date", "pk"))
        current_step = min(self.current_milestone_step, len(milestones))
        for index, milestone in enumerate(milestones, start=1):
            if current_step == 0 or index > current_step:
                milestone_status = ConstructionMilestone.STATUS_PLANNED
            elif index < current_step:
                milestone_status = ConstructionMilestone.STATUS_DONE
            else:
                milestone_status = ConstructionMilestone.STATUS_IN_PROGRESS
            if milestone.milestone_status != milestone_status:
                milestone.milestone_status = milestone_status
                milestone.save(update_fields=["milestone_status", "updated_at"])


class GivingTier(PublishableModel):
    campaign = models.ForeignKey(FundraisingCampaign, on_delete=models.CASCADE, related_name="giving_tiers")
    title_en = models.CharField(max_length=160)
    title_ro = models.CharField(max_length=160, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description_en = models.TextField(blank=True)
    description_ro = models.TextField(blank=True)
    button_url = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "amount"]

    def __str__(self):
        return self.title_en


class ConstructionMilestone(PublishableModel):
    STATUS_PLANNED = "planned"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DONE = "done"
    MILESTONE_CHOICES = [
        (STATUS_PLANNED, "Planned"),
        (STATUS_IN_PROGRESS, "In progress"),
        (STATUS_DONE, "Completed"),
    ]

    campaign = models.ForeignKey(FundraisingCampaign, on_delete=models.CASCADE, related_name="milestones")
    title_en = models.CharField(max_length=180)
    title_ro = models.CharField(max_length=180, blank=True)
    description_en = models.TextField(blank=True)
    description_ro = models.TextField(blank=True)
    target_date = models.DateField(null=True, blank=True)
    completed_date = models.DateField(null=True, blank=True)
    milestone_status = models.CharField(max_length=30, choices=MILESTONE_CHOICES, default=STATUS_PLANNED)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "target_date"]

    def __str__(self):
        return self.title_en


class ConstructionUpdate(PublishableModel):
    campaign = models.ForeignKey(FundraisingCampaign, on_delete=models.CASCADE, related_name="updates")
    title_en = models.CharField(max_length=180)
    title_ro = models.CharField(max_length=180, blank=True)
    body_en = models.TextField(blank=True)
    body_ro = models.TextField(blank=True)
    update_date = models.DateField(default=timezone.localdate)
    image = models.ForeignKey(ImageAsset, on_delete=models.SET_NULL, null=True, blank=True)
    image_static = models.CharField(max_length=255, blank=True)
    featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["-featured", "-update_date", "-publish_at"]

    def __str__(self):
        return self.title_en


class DonationMethod(PublishableModel):
    TYPE_BANK = "bank"
    TYPE_QR = "qr"
    TYPE_ONLINE = "online"
    TYPE_CHOICES = [
        (TYPE_BANK, "Bank transfer"),
        (TYPE_QR, "QR code"),
        (TYPE_ONLINE, "Online donation"),
    ]

    title_en = models.CharField(max_length=180)
    title_ro = models.CharField(max_length=180, blank=True)
    method_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default=TYPE_ONLINE)
    description_en = models.TextField(blank=True)
    description_ro = models.TextField(blank=True)
    details = models.TextField(blank=True, help_text="Use one detail per line, such as IBAN, account name, or charity number.")
    button_text_en = models.CharField(max_length=80, blank=True)
    button_text_ro = models.CharField(max_length=80, blank=True)
    button_url = models.URLField(blank=True)
    qr_image = models.ForeignKey(ImageAsset, on_delete=models.SET_NULL, null=True, blank=True)
    qr_image_static = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "title_en"]

    def __str__(self):
        return self.title_en


class NewsletterSubscription(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=120, blank=True)
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default=LANGUAGE_ENGLISH)
    categories = models.JSONField(default=list, blank=True)
    consent_given = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return self.email


class NewsletterIssue(AuditModel):
    STATUS_DRAFT = "draft"
    STATUS_SENT = "sent"
    NEWSLETTER_STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SENT, "Sent"),
    ]

    category = models.CharField(max_length=30, choices=NEWSLETTER_CATEGORIES, default="general")
    subject_en = models.CharField(max_length=180)
    subject_ro = models.CharField(max_length=180, blank=True)
    preview_text_en = models.CharField(max_length=255, blank=True)
    preview_text_ro = models.CharField(max_length=255, blank=True)
    body_text_en = models.TextField("Plain text body in English", blank=True)
    body_text_ro = models.TextField("Plain text body in Romanian", blank=True)
    body_html_en = models.TextField("HTML body in English", blank=True)
    body_html_ro = models.TextField("HTML body in Romanian", blank=True)
    status = models.CharField(max_length=20, choices=NEWSLETTER_STATUS_CHOICES, default=STATUS_DRAFT)
    sent_at = models.DateTimeField(null=True, blank=True)
    recipient_count = models.PositiveIntegerField(default=0)
    last_error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject_en

    def matching_subscribers(self):
        subscribers = NewsletterSubscription.objects.filter(is_active=True, consent_given=True)
        if self.category == "general":
            return subscribers
        return [
            subscriber
            for subscriber in subscribers
            if self.category in (subscriber.categories or [])
        ]

    def send(self):
        from django.core.mail import EmailMultiAlternatives
        from django.template.defaultfilters import linebreaksbr
        from django.urls import reverse

        count = 0
        self.last_error = ""
        try:
            for subscriber in self.matching_subscribers():
                lang = subscriber.preferred_language or LANGUAGE_ENGLISH
                subject = getattr(self, f"subject_{lang}") or self.subject_en
                body_text = getattr(self, f"body_text_{lang}") or self.body_text_en
                body_html = getattr(self, f"body_html_{lang}") or self.body_html_en
                unsubscribe_url = (
                    f"{settings.SITE_URL}"
                    f"{reverse('newsletter_unsubscribe', kwargs={'token': subscriber.unsubscribe_token})}"
                )

                if not body_text:
                    body_text = "Please view this update in an email client that supports HTML."
                body_text = f"{body_text}\n\nUnsubscribe: {unsubscribe_url}"

                html_content = body_html or str(linebreaksbr(body_text))
                html_content = (
                    f"{html_content}"
                    f"<hr><p style=\"font-size:12px;color:#666;\">"
                    f"You are receiving this because you subscribed to Mount Zion updates. "
                    f"<a href=\"{unsubscribe_url}\">Unsubscribe</a>.</p>"
                )

                message = EmailMultiAlternatives(
                    subject=subject,
                    body=body_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[subscriber.email],
                )
                message.attach_alternative(html_content, "text/html")
                message.send()
                count += 1
        except Exception as exc:
            self.last_error = str(exc)
            self.save(update_fields=["last_error", "updated_at"])
            raise

        self.status = self.STATUS_SENT
        self.sent_at = timezone.now()
        self.recipient_count = count
        self.save(update_fields=["status", "sent_at", "recipient_count", "last_error", "updated_at"])
        return count


class ContactMessage(models.Model):
    STATUS_NEW = "new"
    STATUS_REVIEWED = "reviewed"
    STATUS_CLOSED = "closed"
    MESSAGE_STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_CLOSED, "Closed"),
    ]

    name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    subject = models.CharField(max_length=160, blank=True)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=MESSAGE_STATUS_CHOICES, default=STATUS_NEW)
    reply_subject = models.CharField(
        max_length=180,
        blank=True,
        help_text="The subject line that will be sent to the visitor.",
    )
    reply_message = models.TextField(
        blank=True,
        help_text="Write the email reply here, then use the send button below.",
    )
    replied_at = models.DateTimeField(null=True, blank=True, editable=False)
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="contact_messages_replied_to",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.email}"


class PrayerRequest(models.Model):
    STATUS_NEW = "new"
    STATUS_PRAYED = "prayed"
    STATUS_ARCHIVED = "archived"
    PRAYER_STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_PRAYED, "Prayed for"),
        (STATUS_ARCHIVED, "Archived"),
    ]

    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    request = models.TextField()
    share_with_team = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=PRAYER_STATUS_CHOICES, default=STATUS_NEW)
    reply_subject = models.CharField(
        max_length=180,
        blank=True,
        help_text="The subject line that will be sent to the visitor.",
    )
    reply_message = models.TextField(
        blank=True,
        help_text="Write the email reply here, then use the send button below.",
    )
    replied_at = models.DateTimeField(null=True, blank=True, editable=False)
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="prayer_requests_replied_to",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Prayer request from {self.name}"


class AdminInvite(AuditModel):
    email = models.EmailField(blank=True, help_text="Optional. Leave blank if the invite can be used by any email address.")
    token = models.CharField(max_length=80, unique=True, default=generate_secure_token, editable=False)
    expires_at = models.DateTimeField(default=default_invite_expiry)
    used_at = models.DateTimeField(null=True, blank=True)
    used_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="used_admin_invites",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email or self.token[:12]

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at > timezone.now()

    def mark_used(self, user):
        self.used_at = timezone.now()
        self.used_by = user
        self.save(update_fields=["used_at", "used_by", "updated_at"])

    def get_signup_path(self):
        return reverse("private_admin_signup", kwargs={"token": self.token})


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default=LANGUAGE_ENGLISH)
    approved_for_members = models.BooleanField(
        default=True,
        help_text="Use this later if the church wants member-only content to require approval.",
    )
    receive_member_updates = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.get_username()


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


post_save.connect(create_user_profile, sender=get_user_model())
