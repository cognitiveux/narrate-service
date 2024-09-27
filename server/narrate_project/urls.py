from django.conf import settings
from django.conf.urls import include
from django.contrib import admin
from django.conf.urls.static import static

from django.urls import (
	path,
	re_path,
)

urlpatterns = [
	re_path(r"^backend/", include("backend.urls")),
]

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
	urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)