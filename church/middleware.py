from django.conf import settings
from django.utils import translation


class AdminEnglishMiddleware:
    """Keep Django's built-in admin wording consistent with the custom English UI."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.admin_prefix = f"/{settings.PRIVATE_ADMIN_PREFIX}/dashboard/"

    def __call__(self, request):
        if request.path.startswith(self.admin_prefix):
            translation.activate("en")
            request.LANGUAGE_CODE = "en"
        return self.get_response(request)
