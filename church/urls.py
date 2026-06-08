from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import LocalizedAuthenticationForm, LocalizedPasswordResetForm, LocalizedSetPasswordForm


urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.generic_page, {"slug": "about"}, name="about"),
    path("services/", views.generic_page, {"slug": "services"}, name="services"),
    path("charity/", views.charity, name="charity"),
    path("building-fund/", views.building_fund, name="building_fund"),
    path("events/", views.events, name="events"),
    path("events/<slug:slug>/", views.event_detail, name="event_detail"),
    path("contact/", views.contact, name="contact"),
    path("members/", views.MemberUpdatesView.as_view(), name="member_updates"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("newsletter/unsubscribe/<uuid:token>/", views.newsletter_unsubscribe, name="newsletter_unsubscribe"),
    path("language/<str:language_code>/", views.set_language, name="set_language"),
    path("accounts/signup/", views.PublicSignupView.as_view(), name="signup"),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=LocalizedAuthenticationForm,
        ),
        name="login",
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "accounts/password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            form_class=LocalizedPasswordResetForm,
        ),
        name="password_reset",
    ),
    path(
        "accounts/password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            form_class=LocalizedSetPasswordForm,
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("pages/<slug:slug>/", views.generic_page, name="page"),
]
