import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone, translation
from django.views.generic import FormView, TemplateView

from .forms import (
    AdminSignupForm,
    ContactForm,
    LocalizedAuthenticationForm,
    NewsletterSignupForm,
    PrayerRequestForm,
    PublicSignupForm,
)
from .emailing import send_church_notification
from .models import (
    AdminInvite,
    Announcement,
    ConstructionUpdate,
    DonationMethod,
    Event,
    FundraisingCampaign,
    Page,
    ServiceTime,
    SiteSettings,
    TeamMember,
)


def get_page(slug):
    return get_object_or_404(Page, slug=slug, is_visible=True)


def page_sections(page, user):
    if not page:
        return []
    return page.sections.visible_to(user)


def page_blocks(page):
    if not page:
        return {}
    return {block.key: block for block in page.blocks.all()}


def primary_campaign(user):
    return FundraisingCampaign.objects.visible_to(user).filter(is_primary=True).first()


def construction_progress(campaign, user):
    if not campaign:
        return [], 0, 0, 0

    milestones = list(campaign.milestones.visible_to(user))
    total_steps = len(milestones)
    current_step = min(campaign.current_milestone_step, total_steps)
    for index, milestone in enumerate(milestones, start=1):
        if current_step == 0 or index > current_step:
            milestone.display_status = "planned"
        elif index < current_step:
            milestone.display_status = "done"
        else:
            milestone.display_status = "in_progress"

    percent = int((current_step / total_steps) * 100) if total_steps else 0
    return milestones, current_step, total_steps, percent


class AdminSecretLoginView(LoginView):
    template_name = "registration/admin_login.html"
    authentication_form = LocalizedAuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect("admin:index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        if not user.is_staff:
            form.add_error(None, "This login is only for church website administrators.")
            return self.form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("admin:index")


class AdminSignupView(FormView):
    template_name = "registration/admin_signup.html"
    form_class = AdminSignupForm

    def dispatch(self, request, *args, **kwargs):
        self.invite = get_object_or_404(AdminInvite, token=kwargs["token"])
        if not self.invite.is_valid:
            raise Http404("This admin invite is no longer valid.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def form_valid(self, form):
        if self.invite.email and self.invite.email.lower() != form.cleaned_data["email"].lower():
            form.add_error("email", "This invite was created for a different email address.")
            return self.form_invalid(form)
        user = form.save()
        self.invite.mark_used(user)
        messages.success(self.request, "Admin account created. You can now manage the website.")
        login(self.request, user)
        return redirect("admin:index")


class PublicSignupView(FormView):
    template_name = "registration/signup.html"
    form_class = PublicSignupForm
    success_url = reverse_lazy("member_updates")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Welcome. Your account has been created.")
        return super().form_valid(form)


def set_language(request, language_code):
    language_code = language_code if language_code in {"en", "ro"} else "en"
    translation.activate(language_code)
    request.session["django_language"] = language_code
    response = redirect(request.META.get("HTTP_REFERER") or reverse("home"))
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language_code)
    return response


def home(request):
    page = get_page("home")
    campaign = primary_campaign(request.user)
    featured_update = None
    if campaign:
        featured_update = campaign.updates.visible_to(request.user).filter(featured=True).first()
    context = {
        "page": page,
        "sections": page_sections(page, request.user),
        "page_blocks": page_blocks(page),
        "service_times": ServiceTime.objects.filter(is_visible=True),
        "team_members": TeamMember.objects.visible_to(request.user),
        "featured_event": Event.objects.visible_to(request.user).filter(featured=True).first(),
        "campaign": campaign,
        "featured_update": featured_update,
        "newsletter_form": NewsletterSignupForm(),
    }
    return render(request, "church/home.html", context)


def generic_page(request, slug):
    page = get_object_or_404(Page, slug=slug, is_visible=True)
    if slug == "home":
        return redirect("home")
    return render(
        request,
        "church/page.html",
        {
            "page": page,
            "sections": page_sections(page, request.user),
            "page_blocks": page_blocks(page),
        },
    )


def charity(request):
    page = get_page("charity")
    campaign = primary_campaign(request.user)
    context = {
        "page": page,
        "sections": page_sections(page, request.user),
        "page_blocks": page_blocks(page),
        "campaign": campaign,
        "donation_methods": DonationMethod.objects.visible_to(request.user),
        "newsletter_form": NewsletterSignupForm(),
    }
    return render(request, "church/charity.html", context)


def building_fund(request):
    page = get_page("building")
    campaign = primary_campaign(request.user)
    milestones = []
    updates = []
    giving_tiers = []
    current_step = 0
    total_steps = 0
    construction_percent = 0
    if campaign:
        milestones, current_step, total_steps, construction_percent = construction_progress(
            campaign, request.user
        )
        updates = campaign.updates.visible_to(request.user)
        giving_tiers = campaign.giving_tiers.visible_to(request.user)
    context = {
        "page": page,
        "campaign": campaign,
        "sections": page_sections(page, request.user),
        "page_blocks": page_blocks(page),
        "milestones": milestones,
        "current_step": current_step,
        "total_steps": total_steps,
        "construction_percent": construction_percent,
        "updates": updates,
        "giving_tiers": giving_tiers,
        "donation_methods": DonationMethod.objects.visible_to(request.user),
    }
    return render(request, "church/building_fund.html", context)


def events(request):
    page = get_page("events")
    context = {
        "page": page,
        "events": Event.objects.visible_to(request.user),
        "sections": page_sections(page, request.user),
        "page_blocks": page_blocks(page),
    }
    return render(request, "church/events.html", context)


def event_detail(request, slug):
    event = get_object_or_404(Event.objects.visible_to(request.user), slug=slug)
    return render(
        request,
        "church/event_detail.html",
        {
            "event": event,
            "event_images": event.images.filter(is_visible=True),
        },
    )


def contact(request):
    page = get_page("contact")
    contact_form = ContactForm(prefix="contact")
    prayer_form = PrayerRequestForm(prefix="prayer")

    if request.method == "POST":
        if "contact_submit" in request.POST:
            contact_form = ContactForm(request.POST, prefix="contact")
            if contact_form.is_valid():
                message = contact_form.save()
                try:
                    send_church_notification(
                        subject=f"New contact message: {message.subject or message.name}",
                        body=(
                            f"Name: {message.name}\n"
                            f"Email: {message.email}\n"
                            f"Phone: {message.phone or 'Not provided'}\n"
                            f"Subject: {message.subject or 'No subject'}\n\n"
                            f"{message.message}"
                        ),
                        reply_to=message.email,
                    )
                except Exception:
                    logging.getLogger(__name__).exception(
                        "Could not email the church about contact message %s.",
                        message.pk,
                    )
                messages.success(request, "Thank you. Your message has been received.")
                return redirect("contact")
        elif "prayer_submit" in request.POST:
            prayer_form = PrayerRequestForm(request.POST, prefix="prayer")
            if prayer_form.is_valid():
                prayer = prayer_form.save()
                try:
                    send_church_notification(
                        subject=f"New prayer request from {prayer.name}",
                        body=(
                            f"Name: {prayer.name}\n"
                            f"Email: {prayer.email or 'Not provided'}\n"
                            f"Share with prayer team: {'Yes' if prayer.share_with_team else 'No'}\n\n"
                            f"{prayer.request}"
                        ),
                        reply_to=prayer.email or None,
                    )
                except Exception:
                    logging.getLogger(__name__).exception(
                        "Could not email the church about prayer request %s.",
                        prayer.pk,
                    )
                messages.success(request, "Thank you. Your prayer request has been received.")
                return redirect("contact")

    return render(
        request,
        "church/contact.html",
        {
            "page": page,
            "sections": page_sections(page, request.user),
            "page_blocks": page_blocks(page),
            "contact_form": contact_form,
            "prayer_form": prayer_form,
        },
    )


class MemberUpdatesView(LoginRequiredMixin, TemplateView):
    template_name = "church/member_updates.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = get_page("member-updates")
        context["page"] = page
        context["page_blocks"] = page_blocks(page)
        context["announcements"] = Announcement.objects.visible_to(self.request.user)
        campaign = primary_campaign(self.request.user)
        context["campaign"] = campaign
        context["updates"] = campaign.updates.visible_to(self.request.user) if campaign else []
        context["events"] = Event.objects.visible_to(self.request.user)[:6]
        return context


def newsletter_subscribe(request):
    if request.method != "POST":
        return redirect("home")
    form = NewsletterSignupForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "You are subscribed to Mount Zion updates.")
    else:
        messages.error(request, "Please check the newsletter form and try again.")
    return redirect(request.META.get("HTTP_REFERER") or reverse("home"))


def newsletter_unsubscribe(request, token):
    from .models import NewsletterSubscription

    subscription = get_object_or_404(NewsletterSubscription, unsubscribe_token=token)
    subscription.is_active = False
    subscription.save(update_fields=["is_active", "updated_at"])
    return render(request, "church/newsletter_unsubscribe.html", {"subscription": subscription})
