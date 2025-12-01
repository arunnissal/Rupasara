from django.contrib import admin
from django.urls import path, include

# ⭐ Add this import ↓
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gallery.urls')),
]

# ⭐ Add this block to enable static files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
