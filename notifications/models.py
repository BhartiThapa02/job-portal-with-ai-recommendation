from django.db import models
from django.conf import settings


class Notification(models.Model):
    """Notification Model"""
    NOTIFICATION_TYPES = [
        ('application_submitted', 'Application Submitted'),
        ('application_update', 'Application Status Update'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('job_recommendation', 'Job Recommendation'),
        ('new_job_match', 'New Job Match'),
        ('message', 'Message'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='system')
    is_read = models.BooleanField(default=False)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"

