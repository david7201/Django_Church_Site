from django import template
from django.contrib.auth import get_user_model
from django.urls import reverse

from church.models import (
    Announcement,
    ContactMessage,
    Event,
    FundraisingCampaign,
    NewsletterIssue,
    NewsletterSubscription,
    Page,
    PrayerRequest,
    STATUS_DRAFT,
)


register = template.Library()


@register.simple_tag
def admin_dashboard_data():
    campaign = FundraisingCampaign.objects.filter(is_primary=True).first()
    campaign_percent = campaign.progress_percent if campaign else 0
    campaign_raised = campaign.raised_amount if campaign else 0
    campaign_goal = campaign.goal_amount if campaign else 0

    return {
        "subscriber_count": NewsletterSubscription.objects.filter(is_active=True).count(),
        "new_contact_count": ContactMessage.objects.filter(
            status=ContactMessage.STATUS_NEW
        ).count(),
        "new_prayer_count": PrayerRequest.objects.filter(
            status=PrayerRequest.STATUS_NEW
        ).count(),
        "draft_announcement_count": Announcement.objects.filter(status=STATUS_DRAFT).count(),
        "draft_event_count": Event.objects.filter(status=STATUS_DRAFT).count(),
        "draft_newsletter_count": NewsletterIssue.objects.filter(
            status=NewsletterIssue.STATUS_DRAFT
        ).count(),
        "page_count": Page.objects.count(),
        "admin_count": get_user_model().objects.filter(is_staff=True, is_active=True).count(),
        "campaign_percent": campaign_percent,
        "campaign_raised": campaign_raised,
        "campaign_goal": campaign_goal,
        "home_url": reverse("home"),
        "pages_url": reverse("admin:church_page_changelist"),
        "homepage_url": (
            reverse("admin:church_page_change", args=[Page.objects.get(slug="home").pk])
            if Page.objects.filter(slug="home").exists()
            else reverse("admin:church_page_changelist")
        ),
        "site_settings_url": reverse("admin:church_sitesettings_changelist"),
        "announcements_add_url": reverse("admin:church_announcement_add"),
        "events_add_url": reverse("admin:church_event_add"),
        "newsletter_add_url": reverse("admin:church_newsletterissue_add"),
        "images_add_url": reverse("admin:church_imageasset_add"),
    }
