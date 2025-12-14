from django.urls import path
from . import admin_views

app_name = 'core'

urlpatterns = [
    path('admin/analytics/', admin_views.admin_analytics, name='admin_analytics'),
    path('admin/update-analytics/', admin_views.update_analytics, name='update_analytics'),
]

