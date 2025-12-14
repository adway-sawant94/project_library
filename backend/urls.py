from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Core app URLs - all main functionality
    path('', include('core.urls', namespace='core')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site header and title
admin.site.site_header = "ProjectLibrary Admin"
admin.site.site_title = "ProjectLibrary Admin Portal"
admin.site.index_title = "Welcome to ProjectLibrary Admin"