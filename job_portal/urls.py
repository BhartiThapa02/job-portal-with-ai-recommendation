"""
URL configuration for job_portal project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('api/', include('jobs.api_urls')),
    path('api/', include('applications.api_urls')),
    path('api/', include('companies.api_urls')),
    path('api/', include('accounts.api_urls')),
    path('', include('jobs.urls')),
    path('companies/', include('companies.urls')),
    path('applications/', include('applications.urls')),
    path('notifications/', include('notifications.urls')),
    path('', include('core.urls')),
    # OAuth URLs (uncomment when django-allauth is installed)
    # path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # In DEBUG mode, Django's staticfiles app automatically serves from STATICFILES_DIRS
    # But we add this as a fallback to ensure static files are served
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    # Direct favicon route for browsers that request /favicon.ico
    urlpatterns += [
        path('favicon.ico', RedirectView.as_view(url=settings.STATIC_URL + 'images/job_portal.png', permanent=True)),
    ]

