from django.contrib import admin
from .models import Application, ApplicationMessage


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'status', 'applied_at', 'interview_date']
    list_filter = ['status', 'applied_at', 'interview_date']
    search_fields = ['user__email', 'job__title', 'job__company__name']
    readonly_fields = ['applied_at', 'updated_at']
    list_editable = ['status']


@admin.register(ApplicationMessage)
class ApplicationMessageAdmin(admin.ModelAdmin):
    list_display = ['application', 'sender', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['application__job__title', 'sender__email']

