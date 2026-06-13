import os
from pathlib import Path
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


DEBUG = env_bool("DEBUG", False)

SECRET_KEY = os.getenv("SECRET_KEY", "")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "").strip("/")

if DEBUG:
    SECRET_KEY = SECRET_KEY or "django-insecure-local-development-only"
    ADMIN_SECRET = ADMIN_SECRET or "local-admin-development-only"
else:
    if len(SECRET_KEY) < 50 or any(
        marker in SECRET_KEY.lower() for marker in ("change-this", "unsafe", "development")
    ):
        raise ImproperlyConfigured("A strong SECRET_KEY must be supplied in production.")
    if (
        len(ADMIN_SECRET) < 40
        or any(marker in ADMIN_SECRET.lower() for marker in ("change-this", "admin-secret", "development"))
        or not all(character.isalnum() or character in "-_" for character in ADMIN_SECRET)
    ):
        raise ImproperlyConfigured(
            "ADMIN_SECRET must be a private URL-safe random value of at least 40 characters."
        )

ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1,testserver" if DEBUG else "",
)
if not DEBUG and (not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS):
    raise ImproperlyConfigured(
        "Production ALLOWED_HOSTS must list the website's exact hostnames."
    )

SITE_URL = os.getenv("SITE_URL", "http://localhost:8000" if DEBUG else "").rstrip("/")
if not DEBUG and (not SITE_URL or not SITE_URL.startswith("https://")):
    raise ImproperlyConfigured("Production SITE_URL must use HTTPS.")

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
if not DEBUG and not CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS = [SITE_URL]
if not DEBUG and any(not origin.startswith("https://") for origin in CSRF_TRUSTED_ORIGINS):
    raise ImproperlyConfigured("Production CSRF_TRUSTED_ORIGINS must use HTTPS.")

PRIVATE_ADMIN_PREFIX = f"mz-private-control/{ADMIN_SECRET}"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "church",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "church.middleware.SecurityHeadersMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "church.middleware.AdminEnglishMiddleware",
    "django.middleware.common.CommonMiddleware",
    "church.middleware.LocalDevelopmentOriginMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "church.middleware.RateLimitMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mount_zion.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "church.context_processors.site_context",
            ],
        },
    },
]

WSGI_APPLICATION = "mount_zion.wsgi.application"

AUTHENTICATION_BACKENDS = [
    "church.auth_backends.StaffAdminBackend",
]


def database_config():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        if not DEBUG:
            raise ImproperlyConfigured("DATABASE_URL must be supplied in production.")
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }

    parsed = urlparse(database_url)
    engine = "django.db.backends.postgresql" if parsed.scheme.startswith("postgres") else parsed.scheme
    return {
        "ENGINE": engine,
        "NAME": parsed.path.lstrip("/"),
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "",
        "PORT": parsed.port or "",
    }


DATABASES = {"default": database_config()}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]
PASSWORD_RESET_TIMEOUT = 60 * 60

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", "English"),
    ("ro", "Romanian"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
TIME_ZONE = "Europe/Dublin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    ("assets", BASE_DIR / "assets"),
    ("css", BASE_DIR / "css"),
    ("js", BASE_DIR / "js"),
    ("logo", BASE_DIR / "logo"),
    BASE_DIR / "static",
]
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}
WHITENOISE_MAX_AGE = 31536000 if not DEBUG else 0

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
FILE_UPLOAD_PERMISSIONS = 0o640
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o750
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1500

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "member_updates"
LOGOUT_REDIRECT_URL = "home"

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "Mount Zion Church <mountziondublin@gmail.com>",
)
SERVER_EMAIL = os.getenv("SERVER_EMAIL", DEFAULT_FROM_EMAIL)
CHURCH_NOTIFICATION_EMAIL = os.getenv(
    "CHURCH_NOTIFICATION_EMAIL",
    "mountziondublin@gmail.com",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp-relay.brevo.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", "20"))
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
    else "django.core.mail.backends.console.EmailBackend",
)

if not DEBUG and (
    not EMAIL_HOST_USER
    or not EMAIL_HOST_PASSWORD
    or EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend"
):
    raise ImproperlyConfigured(
        "Production email credentials must be configured so private reset links are not logged."
    )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", not DEBUG)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000" if not DEBUG else "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", not DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Lax"
LANGUAGE_COOKIE_SECURE = not DEBUG
LANGUAGE_COOKIE_HTTPONLY = True
LANGUAGE_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"

TRUST_X_FORWARDED_FOR = env_bool("TRUST_X_FORWARDED_FOR", False)
REQUEST_RATE_LIMITS = {
    "login": (10, 15 * 60),
    "password_reset": (5, 60 * 60),
    "signup": (5, 60 * 60),
    "forms": (20, 60 * 60),
}
