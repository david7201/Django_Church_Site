from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from church.views import AdminSecretLoginView, AdminSignupView


urlpatterns = [
    path("", include("church.urls")),
    path(
        f"{settings.PRIVATE_ADMIN_PREFIX}/login/",
        AdminSecretLoginView.as_view(),
        name="private_admin_login",
    ),
    path(
        f"{settings.PRIVATE_ADMIN_PREFIX}/signup/<str:token>/",
        AdminSignupView.as_view(),
        name="private_admin_signup",
    ),
    path(f"{settings.PRIVATE_ADMIN_PREFIX}/dashboard/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
