from django.conf import settings
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.static import serve as serve_static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.api_urls")),
    # Serve i file media (loghi aziendali) sempre, non solo in DEBUG:
    # per il volume di traffico di questa applicazione va benissimo,
    # se in futuro servisse di piu' si puo' spostare su nginx-proxy.
    re_path(r"^media/(?P<path>.*)$", serve_static, {"document_root": settings.MEDIA_ROOT}),
]
