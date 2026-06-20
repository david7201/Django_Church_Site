import hashlib
from urllib.parse import urlsplit

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse


class LocalDevelopmentOriginMiddleware:
    """Handle Origin: null where the browser still submits a valid CSRF token."""

    LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}

    def __init__(self, get_response):
        self.get_response = get_response
        self.private_prefix = f"/{settings.PRIVATE_ADMIN_PREFIX}/"

    def __call__(self, request):
        hostname = urlsplit(f"//{request.get_host()}").hostname
        if (
            request.META.get("HTTP_ORIGIN") == "null"
            and (
                request.path.startswith(self.private_prefix)
                or (settings.DEBUG and hostname in self.LOOPBACK_HOSTS)
            )
        ):
            request.META.pop("HTTP_ORIGIN")
        return self.get_response(request)


class SecurityHeadersMiddleware:
    """Add browser security headers and prevent caching of sensitive pages."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.private_prefix = f"/{settings.PRIVATE_ADMIN_PREFIX}/"

    def __call__(self, request):
        response = self.get_response(request)
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "base-uri 'self'; "
            "connect-src 'self'; "
            "font-src 'self' https://fonts.gstatic.com https://use.fontawesome.com data:; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "img-src 'self' data: https:; "
            "object-src 'none'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://use.fontawesome.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;"
            + (" upgrade-insecure-requests;" if not settings.DEBUG else ""),
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
        )
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-site")
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        sensitive_path = (
            request.path.startswith(self.private_prefix)
            or request.path.startswith("/accounts/reset/")
            or request.path.startswith("/accounts/password-reset")
            or request.path.startswith("/members/")
        )
        if sensitive_path:
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Referrer-Policy"] = "same-origin"
        return response


class RateLimitMiddleware:
    """Apply lightweight per-client throttling to authentication and public forms."""

    def __init__(self, get_response):
        self.get_response = get_response
        prefix = f"/{settings.PRIVATE_ADMIN_PREFIX}"
        self.login_paths = {
            "/accounts/login/",
            f"{prefix}/login/",
            f"{prefix}/dashboard/login/",
        }
        self.password_reset_paths = {"/accounts/password-reset/"}
        self.signup_prefixes = ("/accounts/signup/", f"{prefix}/signup/")
        self.form_paths = {"/contact/", "/newsletter/subscribe/"}

    def __call__(self, request):
        rule_name = self._rule_name(request)
        if rule_name and self._is_limited(request, rule_name):
            limit, period = settings.REQUEST_RATE_LIMITS[rule_name]
            response = HttpResponse(
                "Too many attempts. Please wait before trying again.",
                status=429,
                content_type="text/plain; charset=utf-8",
            )
            response.headers["Retry-After"] = str(period)
            response.headers["Cache-Control"] = "no-store"
            return response
        return self.get_response(request)

    def _rule_name(self, request):
        if request.method != "POST":
            return None
        if request.path in self.login_paths:
            return "login"
        if request.path in self.password_reset_paths:
            return "password_reset"
        if request.path.startswith(self.signup_prefixes):
            return "signup"
        if request.path in self.form_paths:
            return "forms"
        return None

    def _client_identifier(self, request, rule_name):
        remote_address = request.META.get("REMOTE_ADDR", "unknown")
        if settings.TRUST_X_FORWARDED_FOR:
            forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
            if forwarded_for:
                remote_address = forwarded_for.split(",", 1)[0].strip()

        submitted_identity = ""
        if rule_name == "login":
            submitted_identity = request.POST.get("username", "")
        elif rule_name == "password_reset":
            submitted_identity = request.POST.get("email", "")

        raw_identifier = f"{remote_address}|{submitted_identity.lower().strip()}"
        return hashlib.sha256(raw_identifier.encode("utf-8")).hexdigest()

    def _is_limited(self, request, rule_name):
        limit, period = settings.REQUEST_RATE_LIMITS[rule_name]
        identifier = self._client_identifier(request, rule_name)
        cache_key = f"request-limit:{rule_name}:{identifier}"
        if cache.add(cache_key, 1, timeout=period):
            return False
        try:
            attempts = cache.incr(cache_key)
        except ValueError:
            cache.set(cache_key, 1, timeout=period)
            attempts = 1
        return attempts > limit
