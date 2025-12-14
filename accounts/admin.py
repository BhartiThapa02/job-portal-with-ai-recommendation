from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, JobSeekerProfile, SavedJob, PasswordResetToken, EmailVerificationToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'user_type', 'is_email_verified', 'is_approved', 'is_suspended', 'is_banned', 'date_joined']
    list_filter = ['user_type', 'is_email_verified', 'is_approved', 'is_suspended', 'is_banned', 'is_staff', 'is_superuser']
    search_fields = ['email', 'username']
    ordering = ['-date_joined']
    
    # Filter to show only employers
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.GET.get('user_type__exact') == 'employer':
            return qs.filter(user_type='employer')
        return qs
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'phone', 'is_email_verified', 'is_approved', 'is_suspended', 'is_banned')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'user_type', 'phone')
        }),
    )
    
    # Add actions for employer management
    actions = ['approve_employers', 'reset_password_action']
    
    def approve_employers(self, request, queryset):
        """Approve selected employer accounts"""
        employers = queryset.filter(user_type='employer', is_approved=False)
        count = employers.update(is_approved=True)
        self.message_user(request, f'{count} employer account(s) approved.')
    approve_employers.short_description = "Approve selected employers"
    
    def reset_password_action(self, request, queryset):
        """Reset password for selected users"""
        from django.contrib.auth.hashers import make_password
        import secrets
        new_password = secrets.token_urlsafe(12)  # Generate random password
        for user in queryset:
            user.set_password(new_password)
            user.save()
        self.message_user(request, f'Password reset for {queryset.count()} user(s). New password: {new_password}')
    reset_password_action.short_description = "Reset password (generates new random password)"


@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name', 'location', 'experience_years', 'created_at']
    search_fields = ['first_name', 'last_name', 'user__email']
    list_filter = ['created_at', 'gender']


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['user__email', 'job__title']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'is_used', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['token', 'created_at', 'expires_at']


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'is_used', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['token', 'created_at', 'expires_at']

