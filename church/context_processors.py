from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError
from django.utils.translation import get_language

from .models import Announcement, NEWSLETTER_CATEGORIES, Page, SiteSettings


def site_context(request):
    language = (get_language() or "en").split("-")[0]
    context = {
        "current_language": language,
        "available_languages": settings.LANGUAGES,
        "newsletter_categories": NEWSLETTER_CATEGORIES,
        "private_admin_login_url": f"/{settings.PRIVATE_ADMIN_PREFIX}/login/",
    }

    try:
        context["site_settings"] = SiteSettings.load()
        context["nav_pages"] = Page.objects.filter(is_visible=True, show_in_navigation=True).order_by(
            "navigation_order", "nav_title_en"
        )
        context["active_announcements"] = Announcement.objects.visible_to(request.user).filter(
            is_urgent=True
        )[:3]
    except (OperationalError, ProgrammingError):
        context["site_settings"] = None
        context["nav_pages"] = []
        context["active_announcements"] = []

    return context
