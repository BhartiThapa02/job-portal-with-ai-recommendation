from django.contrib import admin
from .models import Job, JobView, JobRecommendation


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'work_mode', 'job_type', 'is_active', 'is_featured', 'views', 'application_count', 'created_at']
    list_filter = ['is_active', 'is_featured', 'work_mode', 'job_type', 'experience_level', 'created_at']
    search_fields = ['title', 'company__name', 'location']
    readonly_fields = ['views', 'application_count', 'created_at', 'updated_at']
    list_editable = ['is_active', 'is_featured']


@admin.register(JobView)
class JobViewAdmin(admin.ModelAdmin):
    list_display = ['job', 'user', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['job__title', 'user__email']


@admin.register(JobRecommendation)
class JobRecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'job__title']

