from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from .emailing import send_request_reply
from .models import (
    AdminInvite,
    Announcement,
    ConstructionMilestone,
    ConstructionUpdate,
    ContactMessage,
    DonationMethod,
    Event,
    EventImage,
    FundraisingCampaign,
    GivingTier,
    ImageAsset,
    NewsletterIssue,
    NewsletterSubscription,
    Page,
    PageBlock,
    PageSection,
    PrayerRequest,
    ServiceTime,
    SiteSettings,
    TeamMember,
    UserProfile,
)


admin.site.site_header = "Mount Zion Website Admin"
admin.site.site_title = "Mount Zion Admin"
admin.site.index_title = "Manage the church website"


class FriendlyAdminMixin:
    pass


class ContactMessageAdminForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if (
            self.instance.pk
            and "reply_subject" in self.fields
            and not self.instance.reply_subject
        ):
            original_subject = self.instance.subject or "Your message to Mount Zion Church"
            self.fields["reply_subject"].initial = f"Re: {original_subject}"


class PrayerRequestAdminForm(forms.ModelForm):
    class Meta:
        model = PrayerRequest
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if (
            self.instance.pk
            and "reply_subject" in self.fields
            and not self.instance.reply_subject
        ):
            self.fields["reply_subject"].initial = "Re: Your prayer request to Mount Zion Church"


class EmailReplyAdminMixin:
    change_form_template = "admin/church/request_message/change_form.html"
    reply_status_after_send = None

    def response_change(self, request, obj):
        if "_send_email_reply" not in request.POST:
            return super().response_change(request, obj)

        recipient = (obj.email or "").strip()
        subject = (obj.reply_subject or "").strip()
        body = (obj.reply_message or "").strip()
        if not recipient:
            self.message_user(
                request,
                "This request does not include an email address, so a reply cannot be sent.",
                messages.ERROR,
            )
            return HttpResponseRedirect(request.path)
        if not subject or not body:
            self.message_user(
                request,
                "Add both a reply subject and message before sending.",
                messages.ERROR,
            )
            return HttpResponseRedirect(request.path)

        try:
            send_request_reply(recipient, subject, body)
        except Exception as exc:
            self.message_user(
                request,
                f"The reply was saved but could not be sent: {exc}",
                messages.ERROR,
            )
            return HttpResponseRedirect(request.path)

        obj.replied_at = timezone.now()
        obj.replied_by = request.user
        update_fields = ["replied_at", "replied_by"]
        if self.reply_status_after_send and obj.status != self.reply_status_after_send:
            obj.status = self.reply_status_after_send
            update_fields.append("status")
        obj.save(update_fields=update_fields)
        self.message_user(
            request,
            f"Email reply sent successfully to {recipient}.",
            messages.SUCCESS,
        )
        return HttpResponseRedirect(request.path)


@admin.action(description="Hide selected from the website")
def hide_selected(modeladmin, request, queryset):
    updated = queryset.update(is_visible=False)
    modeladmin.message_user(
        request,
        f"{updated} item{'s were' if updated != 1 else ' was'} hidden. Nothing was deleted.",
        messages.SUCCESS,
    )


@admin.action(description="Show selected on the website")
def show_selected(modeladmin, request, queryset):
    updated = queryset.update(is_visible=True)
    modeladmin.message_user(
        request,
        f"{updated} item{'s are' if updated != 1 else ' is'} now visible.",
        messages.SUCCESS,
    )


class VisibilityAdminMixin:
    actions = (hide_selected, show_selected)


class AuditAdmin(FriendlyAdminMixin, admin.ModelAdmin):
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")

    def save_model(self, request, obj, form, change):
        if hasattr(obj, "updated_by"):
            obj.updated_by = request.user
        if not change and hasattr(obj, "created_by"):
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in instances:
            if hasattr(obj, "updated_by"):
                obj.updated_by = request.user
            if not obj.pk and hasattr(obj, "created_by"):
                obj.created_by = request.user
            obj.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()


class PublishableAdmin(VisibilityAdminMixin, AuditAdmin):
    list_filter = ("is_visible", "status", "visibility", "publish_at", "expires_at")

    @admin.display(description="Status", ordering="status")
    def publishing_status(self, obj):
        labels = {
            "published": "Published",
            "draft": "Draft",
            "archived": "Archived",
        }
        return format_html(
            '<span class="mz-status mz-status-{}">{}</span>',
            obj.status,
            labels.get(obj.status, obj.get_status_display()),
        )

    @admin.display(description="Audience", ordering="visibility")
    def publishing_audience(self, obj):
        labels = {
            "public": "Everyone",
            "members": "Members only",
        }
        return format_html(
            '<span class="mz-status mz-status-{}">{}</span>',
            obj.visibility,
            labels.get(obj.visibility, obj.get_visibility_display()),
        )


@admin.register(ImageAsset)
class ImageAssetAdmin(AuditAdmin):
    list_display = ("thumbnail", "title", "category", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", "alt_text_en", "alt_text_ro", "caption_en", "caption_ro")
    fieldsets = (
        ("Image", {"fields": ("title", "category", "image", "thumbnail")}),
        ("Accessibility and captions", {"fields": ("alt_text_en", "alt_text_ro", "caption_en", "caption_ro")}),
        ("Change history", {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)}),
    )
    readonly_fields = AuditAdmin.readonly_fields + ("thumbnail",)

    def thumbnail(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" class="mz-thumbnail" alt="">', obj.image.url)
        return "No image"


class PageSectionInline(admin.StackedInline):
    model = PageSection
    verbose_name = "Custom page section"
    verbose_name_plural = "Custom page sections"
    extra = 0
    ordering = ("order",)
    fieldsets = (
        (
            "Website visibility",
            {
                "fields": ("is_visible",),
                "description": "Switch this off to hide the section without deleting its text or images.",
            },
        ),
        ("Content", {"fields": ("title_en", "title_ro", "body_en", "body_ro")}),
        ("Display", {"fields": ("layout", "image", "image_static", "button_text_en", "button_text_ro", "button_url", "order")}),
        ("Publishing", {"fields": ("status", "visibility", "publish_at", "expires_at")}),
    )


class PageBlockInline(admin.StackedInline):
    model = PageBlock
    verbose_name = "Built-in page section"
    verbose_name_plural = "Built-in page sections"
    extra = 0
    can_delete = False
    ordering = ("order",)
    readonly_fields = ("label", "key", "manage_section_content")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "label",
                    "is_visible",
                    "title_en",
                    "title_ro",
                    "subtitle_en",
                    "subtitle_ro",
                    "body_en",
                    "body_ro",
                    "image",
                    "image_static",
                    "button_text_en",
                    "button_text_ro",
                    "button_url",
                    "manage_section_content",
                )
            },
        ),
    )

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="Section items")
    def manage_section_content(self, obj):
        if not obj or not obj.pk:
            return "Save the page first."

        links = {
            "service_schedule": ("admin:church_servicetime_changelist", "Manage service times"),
            "fundraising": ("admin:church_fundraisingcampaign_changelist", "Manage campaign amounts and progress"),
            "latest_update": ("admin:church_fundraisingcampaign_changelist", "Manage building updates"),
            "team": ("admin:church_teammember_changelist", "Manage team members"),
            "newsletter": ("admin:church_newslettersubscription_changelist", "View newsletter subscribers"),
            "home_address": ("admin:church_sitesettings_change", "Edit address", (1,)),
            "home_email": ("admin:church_sitesettings_change", "Edit email address", (1,)),
            "home_phone": ("admin:church_sitesettings_change", "Edit phone number", (1,)),
            "donations": ("admin:church_donationmethod_changelist", "Manage donation methods"),
            "giving_tiers": ("admin:church_fundraisingcampaign_changelist", "Manage giving tiers"),
            "milestones": ("admin:church_fundraisingcampaign_changelist", "Manage construction milestones"),
            "updates": ("admin:church_fundraisingcampaign_changelist", "Manage photo updates"),
            "events_listing": ("admin:church_event_changelist", "Manage events and galleries"),
            "contact_address": ("admin:church_sitesettings_change", "Edit address and directions", (1,)),
            "contact_email": ("admin:church_sitesettings_change", "Edit email address", (1,)),
            "contact_phone": ("admin:church_sitesettings_change", "Edit phone number", (1,)),
            "contact_form": ("admin:church_contactmessage_changelist", "View contact messages"),
            "prayer_form": ("admin:church_prayerrequest_changelist", "View prayer requests"),
            "announcements": ("admin:church_announcement_changelist", "Manage announcements"),
            "building_updates": ("admin:church_fundraisingcampaign_changelist", "Manage building updates"),
        }
        link_data = links.get(obj.key)
        if not link_data:
            return "All content for this section is editable above."
        url_name, label, *args_data = link_data
        args = args_data[0] if args_data else None
        return format_html(
            '<a class="button mz-section-manage-link" href="{}">{}</a>',
            reverse(url_name, args=args),
            label,
        )


@admin.register(Page)
class PageAdmin(VisibilityAdminMixin, AuditAdmin):
    list_display = ("nav_title_en", "slug", "is_visible", "show_in_navigation", "navigation_order")
    list_editable = ("is_visible", "show_in_navigation", "navigation_order")
    list_filter = ("is_visible", "show_in_navigation", "show_hero")
    search_fields = ("slug", "nav_title_en", "nav_title_ro", "hero_title_en", "hero_title_ro")
    inlines = [PageBlockInline, PageSectionInline]
    fieldsets = (
        (
            "Website visibility",
            {
                "fields": ("is_visible",),
                "description": "Switch this off to hide the entire page without deleting any content.",
            },
        ),
        ("Page identity", {"fields": ("slug", "nav_title_en", "nav_title_ro", "show_in_navigation", "navigation_order")}),
        ("Search engine preview", {"fields": ("meta_title_en", "meta_title_ro", "meta_description_en", "meta_description_ro")}),
        ("Hero area", {"fields": ("show_hero", "hero_title_en", "hero_title_ro", "hero_subtitle_en", "hero_subtitle_ro", "hero_button_text_en", "hero_button_text_ro", "hero_button_url", "hero_image", "hero_image_static", "body_id")}),
        ("Change history", {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)}),
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(AuditAdmin):
    fieldsets = (
        ("Church identity", {"fields": ("church_name", "tagline_en", "tagline_ro", "logo", "hero_image", "hero_image_static")}),
        ("SEO defaults", {"fields": ("default_meta_title_en", "default_meta_title_ro", "default_meta_description_en", "default_meta_description_ro")}),
        ("Contact details", {"fields": ("address", "email", "phone", "directions_url", "facebook_url", "instagram_url", "youtube_url")}),
        ("Footer", {"fields": ("show_footer", "footer_text_en", "footer_text_ro")}),
        ("Change history", {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)}),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ServiceTime)
class ServiceTimeAdmin(VisibilityAdminMixin, AuditAdmin):
    list_display = ("day_order", "day_en", "service_name_en", "time_text", "is_closed", "is_visible")
    list_display_links = ("day_en",)
    list_editable = ("day_order", "is_visible")
    list_filter = ("is_visible", "is_closed")
    search_fields = ("day_en", "day_ro", "service_name_en", "service_name_ro", "time_text")


@admin.register(TeamMember)
class TeamMemberAdmin(PublishableAdmin):
    list_display = ("name", "role_en", "is_visible", "publishing_status", "publishing_audience", "order")
    list_editable = ("is_visible", "order")
    search_fields = ("name", "role_en", "role_ro", "bio_en", "bio_ro")
    fieldsets = (
        ("Person", {"fields": ("name", "role_en", "role_ro", "bio_en", "bio_ro", "photo", "order")}),
        ("Publishing", {"fields": ("is_visible", "status", "visibility", "publish_at", "expires_at")}),
        ("Change history", {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)}),
    )


@admin.register(Announcement)
class AnnouncementAdmin(PublishableAdmin):
    list_display = (
        "title_en",
        "category",
        "is_visible",
        "is_urgent",
        "publishing_audience",
        "publishing_status",
        "publish_at",
        "expires_at",
    )
    list_editable = ("is_visible",)
    list_filter = ("is_visible", "category", "is_urgent", "status", "visibility")
    search_fields = ("title_en", "title_ro", "body_en", "body_ro")
    fieldsets = (
        ("Announcement", {"fields": ("category", "is_urgent", "title_en", "title_ro", "body_en", "body_ro", "link_text_en", "link_text_ro", "link_url")}),
        (
            "Who can see it?",
            {
                "fields": ("is_visible", "visibility"),
                "description": "Switch Show on website off for a quick temporary hide.",
            },
        ),
        ("When should it appear?", {"fields": ("status", "publish_at", "expires_at")}),
        ("Change history", {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)}),
    )


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 0
    ordering = ("order",)
    fields = ("image", "caption_en", "caption_ro", "order", "is_visible")


@admin.register(Event)
class EventAdmin(PublishableAdmin):
    list_display = (
        "title_en",
        "event_date",
        "is_visible",
        "featured",
        "publishing_audience",
        "publishing_status",
    )
    list_editable = ("is_visible",)
    list_filter = ("is_visible", "featured", "status", "visibility", "event_date")
    search_fields = ("title_en", "title_ro", "summary_en", "summary_ro", "body_en", "body_ro")
    prepopulated_fields = {"slug": ("title_en",)}
    inlines = [EventImageInline]
    fieldsets = (
        (
            "Event sections",
            {
                "fields": ("show_hero", "show_description", "show_gallery"),
                "description": "Hide any event-page section without deleting its content or photos.",
            },
        ),
        ("Event", {"fields": ("title_en", "title_ro", "slug", "event_date", "location_en", "location_ro", "featured")}),
        ("Description", {"fields": ("summary_en", "summary_ro", "body_en", "body_ro")}),
        ("Images", {"fields": ("cover_image", "cover_image_static")}),
        ("Publishing", {"fields": ("is_visible", "status", "visibility", "publish_at", "expires_at")}),
        ("Change history", {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)}),
    )


class GivingTierInline(admin.StackedInline):
    model = GivingTier
    extra = 0
    ordering = ("order",)
    fieldsets = (
        ("Website visibility", {"fields": ("is_visible",)}),
        ("Giving tier", {"fields": ("title_en", "title_ro", "amount", "description_en", "description_ro", "button_url", "order")}),
        ("Publishing", {"fields": ("status", "visibility", "publish_at", "expires_at")}),
    )


class ConstructionMilestoneInline(admin.StackedInline):
    model = ConstructionMilestone
    extra = 0
    ordering = ("order",)
    fields = (
        "title_en",
        "title_ro",
        "description_en",
        "description_ro",
        "target_date",
        "completed_date",
        "order",
        "is_visible",
        "status",
        "visibility",
        "publish_at",
        "expires_at",
    )


class ConstructionUpdateInline(admin.StackedInline):
    model = ConstructionUpdate
    extra = 0
    ordering = ("-update_date",)
    fieldsets = (
        ("Website visibility", {"fields": ("is_visible",)}),
        ("Update", {"fields": ("title_en", "title_ro", "body_en", "body_ro", "update_date", "image", "image_static", "featured")}),
        ("Publishing", {"fields": ("status", "visibility", "publish_at", "expires_at")}),
    )


@admin.register(FundraisingCampaign)
class FundraisingCampaignAdmin(PublishableAdmin):
    list_display = (
        "title_en",
        "is_visible",
        "raised_amount",
        "goal_amount",
        "progress",
        "current_milestone_step",
        "is_primary",
        "publishing_audience",
        "publishing_status",
    )
    list_editable = ("is_visible", "raised_amount", "goal_amount", "current_milestone_step")
    list_filter = ("is_visible", "is_primary", "status", "visibility")
    search_fields = ("title_en", "title_ro", "description_en", "description_ro")
    inlines = [GivingTierInline, ConstructionMilestoneInline, ConstructionUpdateInline]
    fieldsets = (
        (
            "Campaign",
            {
                "fields": (
                    "title_en",
                    "title_ro",
                    "description_en",
                    "description_ro",
                    "goal_amount",
                    "raised_amount",
                    "is_primary",
                ),
                "description": (
                    "The raised amount and goal control the fundraising progress bar. "
                    "They can also be updated directly from the campaign list."
                ),
            },
        ),
        (
            "Construction progress",
            {
                "fields": ("current_milestone_step",),
                "description": (
                    "Change this one number when construction moves to a new stage. "
                    "Milestone markers and the public stage progress bar update automatically."
                ),
            },
        ),
        (
            "Publishing",
            {
                "fields": ("is_visible", "status", "visibility", "publish_at", "expires_at"),
                "description": "Switch Show on website off to hide the campaign and its public sections.",
            },
        ),
        ("Change history", {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)}),
    )

    def progress(self, obj):
        return f"{obj.progress_percent}%"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        obj.sync_milestone_statuses()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        form.instance.sync_milestone_statuses()


@admin.register(DonationMethod)
class DonationMethodAdmin(PublishableAdmin):
    list_display = (
        "title_en",
        "method_type",
        "is_visible",
        "publishing_status",
        "publishing_audience",
        "order",
    )
    list_editable = ("is_visible", "order")
    list_filter = ("is_visible", "method_type", "status", "visibility")
    search_fields = ("title_en", "title_ro", "description_en", "description_ro", "details")
    fieldsets = (
        ("Donation option", {"fields": ("title_en", "title_ro", "method_type", "description_en", "description_ro", "details", "order")}),
        ("Button and QR code", {"fields": ("button_text_en", "button_text_ro", "button_url", "qr_image", "qr_image_static")}),
        ("Publishing", {"fields": ("is_visible", "status", "visibility", "publish_at", "expires_at")}),
        ("Change history", {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)}),
    )


@admin.register(NewsletterSubscription)
class NewsletterSubscriptionAdmin(FriendlyAdminMixin, admin.ModelAdmin):
    list_display = ("email", "name", "preferred_language", "is_active", "consent_given", "subscribed_at")
    list_filter = ("is_active", "consent_given", "preferred_language", "subscribed_at")
    search_fields = ("email", "name")
    readonly_fields = ("unsubscribe_token", "subscribed_at", "updated_at")


@admin.action(description="Send selected draft newsletters")
def send_newsletters(modeladmin, request, queryset):
    sent_count = 0
    for issue in queryset:
        if issue.status == NewsletterIssue.STATUS_SENT:
            messages.warning(request, f"{issue} was already sent, so it was skipped.")
            continue
        try:
            sent_count += issue.send()
        except Exception as exc:
            messages.error(request, f"{issue} could not be sent: {exc}")
    if sent_count:
        messages.success(request, f"Newsletter sent to {sent_count} subscribers.")


@admin.register(NewsletterIssue)
class NewsletterIssueAdmin(AuditAdmin):
    list_display = ("subject_en", "category", "newsletter_status", "recipient_count", "sent_at", "created_at")
    list_filter = ("category", "status", "sent_at")
    search_fields = ("subject_en", "subject_ro", "body_text_en", "body_text_ro", "body_html_en", "body_html_ro")
    actions = [send_newsletters]
    fieldsets = (
        ("Audience", {"fields": ("category", "status")}),
        ("Email subject and preview", {"fields": ("subject_en", "subject_ro", "preview_text_en", "preview_text_ro")}),
        ("Plain text email", {"fields": ("body_text_en", "body_text_ro")}),
        ("Rich HTML email", {"fields": ("body_html_en", "body_html_ro"), "description": "Optional. Admins can paste simple HTML for richer emails."}),
        ("Sending result", {"fields": ("sent_at", "recipient_count", "last_error")}),
        ("Change history", {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)}),
    )
    readonly_fields = AuditAdmin.readonly_fields + ("sent_at", "recipient_count", "last_error")

    @admin.display(description="Status", ordering="status")
    def newsletter_status(self, obj):
        status_class = "published" if obj.status == NewsletterIssue.STATUS_SENT else "draft"
        return format_html(
            '<span class="mz-status mz-status-{}">{}</span>',
            status_class,
            obj.get_status_display(),
        )


@admin.register(ContactMessage)
class ContactMessageAdmin(EmailReplyAdminMixin, FriendlyAdminMixin, admin.ModelAdmin):
    form = ContactMessageAdminForm
    reply_status_after_send = ContactMessage.STATUS_REVIEWED
    list_display = ("name", "email", "subject", "message_status", "replied_at", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("name", "email", "phone", "subject", "message")
    readonly_fields = (
        "name",
        "email",
        "phone",
        "subject",
        "message",
        "created_at",
        "replied_at",
        "replied_by",
    )
    fieldsets = (
        ("Message received", {"fields": ("name", "email", "phone", "subject", "message", "created_at")}),
        ("Workflow", {"fields": ("status",)}),
        (
            "Reply by email",
            {
                "fields": ("reply_subject", "reply_message", "replied_at", "replied_by"),
                "description": (
                    "Write a response, then use the “Save and send email reply” button below. "
                    "A copy is sent from the church mailbox."
                ),
            },
        ),
    )

    @admin.display(description="Status", ordering="status")
    def message_status(self, obj):
        status_class = {
            ContactMessage.STATUS_NEW: "draft",
            ContactMessage.STATUS_REVIEWED: "published",
            ContactMessage.STATUS_CLOSED: "archived",
        }.get(obj.status, "archived")
        return format_html(
            '<span class="mz-status mz-status-{}">{}</span>',
            status_class,
            obj.get_status_display(),
        )


@admin.register(PrayerRequest)
class PrayerRequestAdmin(EmailReplyAdminMixin, FriendlyAdminMixin, admin.ModelAdmin):
    form = PrayerRequestAdminForm
    reply_status_after_send = PrayerRequest.STATUS_PRAYED
    list_display = ("name", "email", "share_with_team", "prayer_status", "replied_at", "created_at")
    list_filter = ("status", "share_with_team", "created_at")
    search_fields = ("name", "email", "request")
    readonly_fields = (
        "name",
        "email",
        "request",
        "share_with_team",
        "created_at",
        "replied_at",
        "replied_by",
    )
    fieldsets = (
        ("Prayer request received", {"fields": ("name", "email", "request", "share_with_team", "created_at")}),
        ("Workflow", {"fields": ("status",)}),
        (
            "Reply by email",
            {
                "fields": ("reply_subject", "reply_message", "replied_at", "replied_by"),
                "description": (
                    "If the visitor provided an email address, write a response and use the "
                    "“Save and send email reply” button below."
                ),
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        if obj and not obj.email:
            return self.fieldsets[:2]
        return self.fieldsets

    @admin.display(description="Status", ordering="status")
    def prayer_status(self, obj):
        status_class = {
            PrayerRequest.STATUS_NEW: "draft",
            PrayerRequest.STATUS_PRAYED: "published",
            PrayerRequest.STATUS_ARCHIVED: "archived",
        }.get(obj.status, "archived")
        return format_html(
            '<span class="mz-status mz-status-{}">{}</span>',
            status_class,
            obj.get_status_display(),
        )


@admin.register(AdminInvite)
class AdminInviteAdmin(AuditAdmin):
    list_display = ("email", "expires_at", "used_at", "signup_link")
    search_fields = ("email", "token")
    readonly_fields = AuditAdmin.readonly_fields + ("token", "used_at", "used_by", "signup_link")
    fieldsets = (
        ("Invite", {"fields": ("email", "expires_at", "signup_link")}),
        ("Security", {"fields": ("token", "used_at", "used_by")}),
        ("Change history", {"fields": ("created_at", "updated_at", "created_by", "updated_by"), "classes": ("collapse",)}),
    )

    def signup_link(self, obj):
        if not obj or not obj.pk:
            return "Save this invite first to generate the signup link."
        return format_html(
            '<a href="{0}{1}" target="_blank">{0}{1}</a>',
            settings.SITE_URL,
            obj.get_signup_path(),
        )


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


class MountZionUserAdmin(UserAdmin):
    inlines = [UserProfileInline]
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    staff_user_fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal information", {"fields": ("first_name", "last_name", "email")}),
        ("Account access", {"fields": ("is_active",)}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    protected_user_fieldsets = (
        (None, {"fields": ("username",)}),
        ("Personal information", {"fields": ("first_name", "last_name", "email")}),
        (
            "Protected administrator account",
            {"fields": ("is_active", "is_staff", "is_superuser")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    @staticmethod
    def is_protected_admin(obj):
        return bool(obj and (obj.is_staff or obj.is_superuser))

    def has_change_permission(self, request, obj=None):
        if (
            obj
            and not request.user.is_superuser
            and self.is_protected_admin(obj)
        ):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if (
            obj
            and not request.user.is_superuser
            and self.is_protected_admin(obj)
        ):
            return False
        return super().has_delete_permission(request, obj)

    def get_fieldsets(self, request, obj=None):
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)
        if self.is_protected_admin(obj):
            return self.protected_user_fieldsets
        if obj:
            return self.staff_user_fieldsets
        return self.add_fieldsets

    def get_inline_instances(self, request, obj=None):
        if (
            obj
            and not request.user.is_superuser
            and self.is_protected_admin(obj)
        ):
            return []
        return super().get_inline_instances(request, obj)

    def delete_model(self, request, obj):
        if not request.user.is_superuser and self.is_protected_admin(obj):
            raise PermissionDenied("Staff and superuser accounts are protected.")
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        if (
            not request.user.is_superuser
            and queryset.filter(Q(is_staff=True) | Q(is_superuser=True)).exists()
        ):
            self.message_user(
                request,
                "Nothing was deleted because the selection included a protected administrator account.",
                messages.ERROR,
            )
            return
        super().delete_queryset(request, queryset)


admin.site.unregister(User)
admin.site.register(User, MountZionUserAdmin)
