from django.contrib import admin
from .models import SiteSettings, Analytics


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'is_active', 'updated_at']
    list_editable = ['is_active']
    
    def has_add_permission(self, request):
        # Only allow one site settings instance
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_users', 'total_jobs', 'total_applications', 'active_jobs']
    list_filter = ['date']
    readonly_fields = ['date', 'total_users', 'total_job_seekers', 'total_employers', 
                      'total_jobs', 'total_applications', 'active_jobs', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

