from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .forms import ContactForm
from .models import (
    AdminInvite,
    Announcement,
    ContactMessage,
    FundraisingCampaign,
    NewsletterIssue,
    NewsletterSubscription,
    Page,
    PageBlock,
    PageSection,
    PrayerRequest,
    SiteSettings,
    STATUS_PUBLISHED,
    VISIBILITY_MEMBERS,
)


class BootstrapContentTests(TestCase):
    def setUp(self):
        call_command("bootstrap_site", verbosity=0)

    def test_bootstrap_creates_main_pages(self):
        self.assertTrue(Page.objects.filter(slug="home").exists())
        self.assertTrue(Page.objects.filter(slug="about").exists())
        self.assertTrue(Page.objects.filter(slug="building").exists())
        self.assertTrue(Page.objects.filter(slug="member-updates").exists())

    def test_every_fixed_page_area_is_present_as_an_admin_block(self):
        expected_blocks = {
            "home": {
                "construction_popup",
                "scripture",
                "service_schedule",
                "fundraising",
                "latest_update",
                "team",
                "newsletter",
                "home_address",
                "home_email",
                "home_phone",
            },
            "charity": {"donations"},
            "building": {"fundraising", "giving_tiers", "milestones", "updates"},
            "events": {"events_listing"},
            "contact": {
                "contact_address",
                "contact_email",
                "contact_phone",
                "contact_form",
                "prayer_form",
            },
            "member-updates": {"announcements", "building_updates"},
        }
        for page_slug, expected_keys in expected_blocks.items():
            with self.subTest(page=page_slug):
                actual_keys = set(
                    PageBlock.objects.filter(page__slug=page_slug).values_list("key", flat=True)
                )
                self.assertEqual(actual_keys, expected_keys)

    def test_public_pages_render(self):
        urls = [
            reverse("home"),
            reverse("about"),
            reverse("services"),
            reverse("charity"),
            reverse("building_fund"),
            reverse("events"),
            reverse("contact"),
            reverse("login"),
            reverse("signup"),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_romanian_language_switch_uses_translated_content(self):
        response = self.client.get(reverse("set_language", kwargs={"language_code": "ro"}), follow=True)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'lang="ro"')
        self.assertContains(response, "Acasă")
        self.assertContains(response, "Fondul de construcție")
        self.assertContains(response, "Muntele Sion")

    def test_signup_newsletter_categories_are_not_wrapped_in_consent_label(self):
        response = self.client.get(reverse("signup"))
        self.assertContains(response, '<fieldset class="mb-4 newsletter-categories newsletter-categories-field">')
        self.assertContains(response, "<legend class=\"form-label\">Newsletter categories</legend>")
        self.assertNotContains(response, "<span>Newsletter categories</span></label>")

    def test_about_page_groups_large_and_value_cards(self):
        response = self.client.get(reverse("about"))
        self.assertEqual(response.content.count(b'class="dynamic-text-card'), 3)
        self.assertEqual(response.content.count(b'class="dynamic-value-card'), 3)
        self.assertContains(response, 'class="row g-4 justify-content-center dynamic-value-grid"')

    def test_homepage_scripture_is_editable_and_translated(self):
        scripture = PageBlock.objects.get(page__slug="home", key="scripture")
        scripture.title_ro = "Mica 4:5"
        scripture.body_ro = "Verset în limba română."
        scripture.save()
        self.client.get(reverse("set_language", kwargs={"language_code": "ro"}))
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Mica 4:5")
        self.assertContains(response, "Verset în limba română.")

    def test_construction_step_controls_timeline_progress(self):
        campaign = FundraisingCampaign.objects.get(is_primary=True)
        campaign.current_milestone_step = 3
        campaign.save()
        campaign.sync_milestone_statuses()

        response = self.client.get(reverse("building_fund"))
        self.assertEqual(response.context["current_step"], 3)
        self.assertEqual(response.context["total_steps"], 4)
        self.assertEqual(response.context["construction_percent"], 75)
        statuses = list(campaign.milestones.values_list("milestone_status", flat=True))
        self.assertEqual(statuses, ["done", "done", "in_progress", "planned"])


class VisibilityTests(TestCase):
    def setUp(self):
        call_command("bootstrap_site", verbosity=0)
        self.private = Announcement.objects.create(
            title_en="Members only update",
            body_en="Private details",
            status=STATUS_PUBLISHED,
            visibility=VISIBILITY_MEMBERS,
            is_urgent=True,
            publish_at=timezone.now(),
        )
        self.user = User.objects.create_user(username="member", email="member@example.com", password="Password123!")

    def test_member_only_announcement_hidden_from_public_home(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "Members only update")

    def test_member_only_announcement_visible_to_logged_in_member_page(self):
        self.client.login(username="member", password="Password123!")
        response = self.client.get(reverse("member_updates"))
        self.assertContains(response, "Members only update")

    def test_member_updates_require_login(self):
        response = self.client.get(reverse("member_updates"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_hidden_page_section_is_not_rendered_or_deleted(self):
        section = PageSection.objects.filter(page__slug="about").first()
        section.is_visible = False
        section.save(update_fields=["is_visible", "updated_at"])

        response = self.client.get(reverse("about"))

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(section, response.context["sections"])
        self.assertNotContains(response, section.body_en)
        self.assertTrue(PageSection.objects.filter(pk=section.pk).exists())

    def test_hidden_page_returns_404_and_is_removed_from_navigation(self):
        page = Page.objects.get(slug="about")
        page.is_visible = False
        page.save(update_fields=["is_visible", "updated_at"])

        self.assertEqual(self.client.get(reverse("about")).status_code, 404)
        response = self.client.get(reverse("home"))
        self.assertNotIn(page, response.context["nav_pages"])

    def test_hidden_published_content_is_excluded_from_live_queryset(self):
        self.private.is_visible = False
        self.private.save(update_fields=["is_visible", "updated_at"])

        self.client.login(username="member", password="Password123!")
        response = self.client.get(reverse("member_updates"))

        self.assertNotContains(response, "Members only update")

    def test_fixed_home_sections_can_be_hidden_from_home_page_blocks(self):
        settings = SiteSettings.load()
        settings.show_footer = False
        settings.save()
        PageBlock.objects.filter(
            page__slug="home",
            key__in=["construction_popup", "scripture", "newsletter"],
        ).update(is_visible=False)

        response = self.client.get(reverse("home"))

        self.assertNotContains(response, 'id="Word"')
        self.assertNotContains(response, 'class="signup-section"')
        self.assertNotContains(response, '<footer')


class AccountAndAdminTests(TestCase):
    def setUp(self):
        call_command("bootstrap_site", verbosity=0)

    def test_public_signup_creates_member_account_and_newsletter_subscription(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "newmember",
                "first_name": "New",
                "last_name": "Member",
                "email": "newmember@example.com",
                "preferred_language": "en",
                "password1": "A-strong-password-123",
                "password2": "A-strong-password-123",
                "receive_newsletter": "on",
                "newsletter_categories": ["general", "building"],
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newmember")
        self.assertFalse(user.is_staff)
        self.assertTrue(NewsletterSubscription.objects.filter(email="newmember@example.com").exists())

    def test_admin_path_is_not_default_admin(self):
        response = self.client.get("/admin/")
        self.assertEqual(response.status_code, 404)

    def test_private_admin_signup_invite_creates_protected_full_staff_user(self):
        invite = AdminInvite.objects.create(email="admin@example.com")
        response = self.client.post(
            invite.get_signup_path(),
            {
                "username": "churchadmin",
                "first_name": "Church",
                "last_name": "Admin",
                "email": "admin@example.com",
                "password1": "A-strong-password-123",
                "password2": "A-strong-password-123",
            },
        )
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="churchadmin")
        invite.refresh_from_db()
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.has_perm("church.change_page"))
        self.assertTrue(user.has_perm("auth.delete_user"))
        self.assertIsNotNone(invite.used_at)

    def test_private_admin_login_rejects_non_staff(self):
        User.objects.create_user(username="member", password="Password123!")
        response = self.client.post(
            reverse("private_admin_login"),
            {"username": "member", "password": "Password123!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "only for church website administrators")

    def test_admin_dashboard_is_task_focused_for_superuser(self):
        admin_user = User.objects.create_superuser(
            username="dashboardadmin",
            email="dashboard@example.com",
            password="Password123!",
        )
        self.client.force_login(admin_user)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Website content")
        self.assertContains(response, "Communications")
        self.assertContains(response, "Fundraising and building")
        self.assertContains(response, "Quick actions")

    def test_staff_has_full_admin_access_but_cannot_change_or_delete_admins(self):
        owner = User.objects.create_superuser(
            username="owner",
            email="owner@example.com",
            password="Password123!",
        )
        staff = User.objects.create_user(
            username="staffadmin",
            email="staff@example.com",
            password="Password123!",
            is_staff=True,
        )
        other_staff = User.objects.create_user(
            username="otherstaff",
            email="otherstaff@example.com",
            password="Password123!",
            is_staff=True,
        )
        member = User.objects.create_user(
            username="memberaccount",
            email="member@example.com",
            password="Password123!",
        )
        self.client.force_login(staff)

        dashboard = self.client.get(reverse("admin:index"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertContains(dashboard, "Website content")
        self.assertTrue(staff.has_perm("church.delete_page"))

        for protected_user in (owner, other_staff, staff):
            change_url = reverse("admin:auth_user_change", args=[protected_user.pk])
            response = self.client.get(change_url)
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'name="_save"')
            self.assertNotContains(response, "deletelink")
            self.assertNotContains(response, "Reset password")
            password_url = reverse(
                "admin:auth_user_password_change",
                args=[protected_user.pk],
            )
            self.assertEqual(self.client.get(password_url).status_code, 403)

            response = self.client.post(
                change_url,
                {
                    "username": protected_user.username,
                    "email": "changed@example.com",
                    "is_active": "",
                },
            )
            self.assertEqual(response.status_code, 403)
            protected_user.refresh_from_db()
            self.assertTrue(protected_user.is_active)
            self.assertNotEqual(protected_user.email, "changed@example.com")

            delete_url = reverse("admin:auth_user_delete", args=[protected_user.pk])
            self.assertEqual(self.client.get(delete_url).status_code, 403)

        member_change_url = reverse("admin:auth_user_change", args=[member.pk])
        response = self.client.get(member_change_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="_save"')
        self.assertContains(response, 'name="is_active"')
        self.assertNotContains(response, 'name="is_staff"')
        self.assertNotContains(response, 'name="is_superuser"')

        member_delete_url = reverse("admin:auth_user_delete", args=[member.pk])
        response = self.client.post(member_delete_url, {"post": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=member.pk).exists())

    def test_staff_bulk_delete_cannot_remove_protected_admin(self):
        owner = User.objects.create_superuser(
            username="protectedowner",
            email="owner@example.com",
            password="Password123!",
        )
        staff = User.objects.create_user(
            username="bulkstaff",
            email="staff@example.com",
            password="Password123!",
            is_staff=True,
        )
        self.client.force_login(staff)
        changelist_url = reverse("admin:auth_user_changelist")

        response = self.client.post(
            changelist_url,
            {
                "action": "delete_selected",
                "_selected_action": [owner.pk],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cannot delete user")
        self.assertContains(response, "permission to delete")
        self.assertTrue(User.objects.filter(pk=owner.pk).exists())

    def test_home_page_admin_contains_every_builtin_home_section(self):
        admin_user = User.objects.create_superuser(
            username="homeeditor",
            email="homeeditor@example.com",
            password="Password123!",
        )
        self.client.force_login(admin_user)
        home = Page.objects.get(slug="home")

        response = self.client.get(reverse("admin:church_page_change", args=[home.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Built-in page sections")
        for label in [
            "Construction popup",
            "Scripture quote",
            "Service schedule",
            "Building fund progress",
            "Latest building update",
            "Team section",
            "Newsletter signup",
            "Homepage address card",
            "Homepage email card",
            "Homepage phone card",
        ]:
            self.assertContains(response, label)
        self.assertContains(response, "Manage service times")
        self.assertContains(response, "Manage campaign amounts and progress")

    def test_admin_can_hide_and_restore_content_without_deleting_it(self):
        admin_user = User.objects.create_superuser(
            username="visibilityadmin",
            email="visibility@example.com",
            password="Password123!",
        )
        section = PageSection.objects.filter(page__slug="about").first()
        self.client.force_login(admin_user)
        changelist_url = reverse("admin:church_page_changelist")

        response = self.client.post(
            changelist_url,
            {
                "action": "hide_selected",
                "_selected_action": [Page.objects.get(slug="about").pk],
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        page = Page.objects.get(slug="about")
        self.assertFalse(page.is_visible)
        self.assertTrue(Page.objects.filter(pk=page.pk).exists())
        self.assertTrue(PageSection.objects.filter(pk=section.pk).exists())

        self.client.post(
            changelist_url,
            {
                "action": "show_selected",
                "_selected_action": [page.pk],
            },
        )
        page.refresh_from_db()
        self.assertTrue(page.is_visible)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="Mount Zion Church <mountziondublin@gmail.com>",
    CHURCH_NOTIFICATION_EMAIL="mountziondublin@gmail.com",
)
class FormAndNewsletterTests(TestCase):
    def setUp(self):
        call_command("bootstrap_site", verbosity=0)

    def test_newsletter_subscription_and_unsubscribe(self):
        response = self.client.post(
            reverse("newsletter_subscribe"),
            {
                "name": "Subscriber",
                "email": "subscriber@example.com",
                "preferred_language": "en",
                "categories": ["general", "fundraising"],
                "consent_given": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        subscription = NewsletterSubscription.objects.get(email="subscriber@example.com")
        self.assertTrue(subscription.is_active)
        response = self.client.get(reverse("newsletter_unsubscribe", kwargs={"token": subscription.unsubscribe_token}))
        self.assertEqual(response.status_code, 200)
        subscription.refresh_from_db()
        self.assertFalse(subscription.is_active)

    def test_contact_form_honeypot_blocks_spam(self):
        form = ContactForm(
            data={
                "name": "Spam",
                "email": "spam@example.com",
                "subject": "Hello",
                "message": "Spam message",
                "website": "https://spam.example",
            }
        )
        self.assertFalse(form.is_valid())

    def test_contact_and_prayer_forms_create_records(self):
        response = self.client.post(
            reverse("contact"),
            {
                "contact-name": "Visitor",
                "contact-email": "visitor@example.com",
                "contact-phone": "",
                "contact-subject": "Question",
                "contact-message": "Can you contact me?",
                "contact_submit": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ContactMessage.objects.filter(email="visitor@example.com").exists())
        self.assertEqual(mail.outbox[-1].to, ["mountziondublin@gmail.com"])
        self.assertEqual(mail.outbox[-1].reply_to, ["visitor@example.com"])
        self.assertIn("Can you contact me?", mail.outbox[-1].body)

        response = self.client.post(
            reverse("contact"),
            {
                "prayer-name": "Visitor",
                "prayer-email": "visitor@example.com",
                "prayer-request": "Please pray for my family.",
                "prayer-share_with_team": "on",
                "prayer_submit": "1",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PrayerRequest.objects.filter(email="visitor@example.com").exists())
        self.assertEqual(mail.outbox[-1].to, ["mountziondublin@gmail.com"])
        self.assertEqual(mail.outbox[-1].reply_to, ["visitor@example.com"])
        self.assertIn("Please pray for my family.", mail.outbox[-1].body)

    def test_newsletter_uses_church_sender(self):
        NewsletterSubscription.objects.create(
            email="subscriber@example.com",
            preferred_language="en",
            categories=["general"],
            consent_given=True,
            is_active=True,
        )
        issue = NewsletterIssue.objects.create(
            category="general",
            subject_en="Church update",
            body_text_en="This is the latest church update.",
        )

        sent_count = issue.send()

        self.assertEqual(sent_count, 1)
        self.assertEqual(mail.outbox[-1].from_email, "Mount Zion Church <mountziondublin@gmail.com>")
        self.assertEqual(mail.outbox[-1].to, ["subscriber@example.com"])


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="Mount Zion Church <mountziondublin@gmail.com>",
    CHURCH_NOTIFICATION_EMAIL="mountziondublin@gmail.com",
)
class AdminEmailReplyTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="emailadmin",
            email="admin@example.com",
            password="Password123!",
        )
        self.client.force_login(self.admin_user)

    def test_admin_can_reply_to_contact_message(self):
        message = ContactMessage.objects.create(
            name="Visitor",
            email="visitor@example.com",
            subject="Question",
            message="Could someone contact me?",
        )

        response = self.client.post(
            reverse("admin:church_contactmessage_change", args=[message.pk]),
            {
                "status": ContactMessage.STATUS_NEW,
                "reply_subject": "Re: Question",
                "reply_message": "Thank you. We will contact you shortly.",
                "_send_email_reply": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        message.refresh_from_db()
        self.assertEqual(message.status, ContactMessage.STATUS_REVIEWED)
        self.assertEqual(message.replied_by, self.admin_user)
        self.assertIsNotNone(message.replied_at)
        self.assertEqual(mail.outbox[-1].to, ["visitor@example.com"])
        self.assertEqual(mail.outbox[-1].reply_to, ["mountziondublin@gmail.com"])

    def test_admin_can_reply_to_prayer_request(self):
        prayer = PrayerRequest.objects.create(
            name="Visitor",
            email="visitor@example.com",
            request="Please pray for my family.",
        )

        response = self.client.post(
            reverse("admin:church_prayerrequest_change", args=[prayer.pk]),
            {
                "status": PrayerRequest.STATUS_NEW,
                "reply_subject": "Re: Your prayer request",
                "reply_message": "Thank you. Our church is praying with you.",
                "_send_email_reply": "1",
            },
        )

        self.assertEqual(response.status_code, 302)
        prayer.refresh_from_db()
        self.assertEqual(prayer.status, PrayerRequest.STATUS_PRAYED)
        self.assertEqual(prayer.replied_by, self.admin_user)
        self.assertIsNotNone(prayer.replied_at)
        self.assertEqual(mail.outbox[-1].to, ["visitor@example.com"])

    def test_prayer_request_without_email_has_no_send_button(self):
        prayer = PrayerRequest.objects.create(
            name="Anonymous visitor",
            email="",
            request="A private request.",
        )

        response = self.client.get(
            reverse("admin:church_prayerrequest_change", args=[prayer.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="_send_email_reply"')
        self.assertNotContains(response, 'name="reply_message"')
        self.assertContains(response, "No email address was provided")
