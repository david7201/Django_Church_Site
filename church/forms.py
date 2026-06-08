from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import get_language

from .models import (
    ContactMessage,
    LANGUAGE_CHOICES,
    NEWSLETTER_CATEGORIES,
    NewsletterSubscription,
    PrayerRequest,
)


FORM_TEXT = {
    "en": {
        "username": "Username",
        "first_name": "First name",
        "last_name": "Last name",
        "email": "Email",
        "preferred_language": "Preferred language",
        "password1": "Password",
        "password2": "Password confirmation",
        "password": "Password",
        "new_password1": "New password",
        "new_password2": "New password confirmation",
        "receive_newsletter": "Receive newsletter",
        "newsletter_categories": "Newsletter categories",
        "name": "Name",
        "phone": "Phone",
        "subject": "Subject",
        "message": "Message",
        "request": "Prayer request",
        "share_with_team": "Share with the prayer team",
        "consent": "I agree to receive church updates and understand I can unsubscribe at any time.",
        "general": "General",
        "fundraising": "Fundraising",
        "youth": "Youth",
        "prayer": "Prayer",
        "services": "Services",
        "building": "Building Updates",
        "password2_help": "Enter the same password as before, for verification.",
    },
    "ro": {
        "username": "Nume de utilizator",
        "first_name": "Prenume",
        "last_name": "Nume",
        "email": "Email",
        "preferred_language": "Limba preferată",
        "password1": "Parolă",
        "password2": "Confirmare parolă",
        "password": "Parolă",
        "new_password1": "Parolă nouă",
        "new_password2": "Confirmare parolă nouă",
        "receive_newsletter": "Doresc newsletter",
        "newsletter_categories": "Categorii newsletter",
        "name": "Nume",
        "phone": "Telefon",
        "subject": "Subiect",
        "message": "Mesaj",
        "request": "Cerere de rugăciune",
        "share_with_team": "Distribuie cu echipa de rugăciune",
        "consent": "Sunt de acord să primesc noutăți de la biserică și înțeleg că mă pot dezabona oricând.",
        "general": "General",
        "fundraising": "Strângere de fonduri",
        "youth": "Tineret",
        "prayer": "Rugăciune",
        "services": "Servicii",
        "building": "Actualizări construcție",
        "password2_help": "Introdu aceeași parolă pentru confirmare.",
    },
}


def form_language():
    return (get_language() or "en").split("-")[0]


def form_text(key):
    language = form_language()
    return FORM_TEXT.get(language, FORM_TEXT["en"]).get(key, FORM_TEXT["en"].get(key, key))


def localized_newsletter_choices():
    return [(value, form_text(value)) for value, _label in NEWSLETTER_CATEGORIES]


class HoneypotFormMixin(forms.Form):
    website = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Spam check failed.")
        return value


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple, forms.HiddenInput)):
                continue
            css_class = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{css_class} form-control".strip()
            if field_name in {"preferred_language"}:
                widget.attrs["class"] = "form-select"

    def localize_fields(self):
        for field_name, field in self.fields.items():
            if field_name in FORM_TEXT["en"]:
                field.label = form_text(field_name)
        if "newsletter_categories" in self.fields:
            self.fields["newsletter_categories"].choices = localized_newsletter_choices()
        if "categories" in self.fields:
            self.fields["categories"].choices = localized_newsletter_choices()


class LocalizedAuthenticationForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.localize_fields()


class LocalizedPasswordResetForm(BootstrapFormMixin, PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.localize_fields()


class LocalizedSetPasswordForm(BootstrapFormMixin, SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.localize_fields()


class PublicSignupForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)
    preferred_language = forms.ChoiceField(choices=LANGUAGE_CHOICES, initial="en")
    receive_newsletter = forms.BooleanField(required=False, initial=True)
    newsletter_categories = forms.MultipleChoiceField(
        choices=NEWSLETTER_CATEGORIES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        initial=[choice[0] for choice in NEWSLETTER_CATEGORIES],
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "preferred_language")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.localize_fields()
        self.fields["password2"].help_text = form_text("password2_help")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account already exists with this email address.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
            user.profile.preferred_language = self.cleaned_data.get("preferred_language", "en")
            user.profile.receive_member_updates = self.cleaned_data.get("receive_newsletter", True)
            user.profile.save()
            if self.cleaned_data.get("receive_newsletter"):
                NewsletterSubscription.objects.update_or_create(
                    email=user.email,
                    defaults={
                        "name": user.get_full_name() or user.username,
                        "preferred_language": user.profile.preferred_language,
                        "categories": self.cleaned_data.get("newsletter_categories") or [],
                        "consent_given": True,
                        "is_active": True,
                    },
                )
        return user


class AdminSignupForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.localize_fields()
        self.fields["password2"].help_text = form_text("password2_help")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user already exists with this email address.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"].lower()
        user.first_name = self.cleaned_data.get("first_name", "")
        user.last_name = self.cleaned_data.get("last_name", "")
        user.is_staff = True
        user.is_superuser = False
        if commit:
            user.save()
        return user


class NewsletterSignupForm(BootstrapFormMixin, HoneypotFormMixin, forms.ModelForm):
    categories = forms.MultipleChoiceField(
        choices=NEWSLETTER_CATEGORIES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        initial=[choice[0] for choice in NEWSLETTER_CATEGORIES],
    )
    consent_given = forms.BooleanField(
        required=True,
    )

    class Meta:
        model = NewsletterSubscription
        fields = ("name", "email", "preferred_language", "categories", "consent_given")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.localize_fields()
        self.fields["consent_given"].label = form_text("consent")

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def save(self, commit=True):
        email = self.cleaned_data["email"]
        subscription, _ = NewsletterSubscription.objects.update_or_create(
            email=email,
            defaults={
                "name": self.cleaned_data.get("name", ""),
                "preferred_language": self.cleaned_data.get("preferred_language", "en"),
                "categories": self.cleaned_data.get("categories") or [],
                "consent_given": self.cleaned_data.get("consent_given", False),
                "is_active": True,
            },
        )
        return subscription


class ContactForm(BootstrapFormMixin, HoneypotFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "subject", "message")
        widgets = {
            "message": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.localize_fields()


class PrayerRequestForm(BootstrapFormMixin, HoneypotFormMixin, forms.ModelForm):
    class Meta:
        model = PrayerRequest
        fields = ("name", "email", "request", "share_with_team")
        widgets = {
            "request": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.localize_fields()
