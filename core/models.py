from django.db import models
from django.conf import settings


class SiteSettings(models.Model):
    """Site-wide settings and SEO configuration"""
    site_name = models.CharField(max_length=200, default='Job Portal')
    site_tagline = models.CharField(max_length=300, blank=True)
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    homepage_content = models.TextField(blank=True, help_text='Homepage content/description')
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    facebook_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Ensure only one active site settings
        if self.is_active:
            SiteSettings.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class Analytics(models.Model):
    """Site analytics data"""
    date = models.DateField()
    total_users = models.IntegerField(default=0)
    total_job_seekers = models.IntegerField(default=0)
    total_employers = models.IntegerField(default=0)
    total_jobs = models.IntegerField(default=0)
    total_applications = models.IntegerField(default=0)
    active_jobs = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Analytics'
        verbose_name_plural = 'Analytics'
        unique_together = ['date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Analytics for {self.date}"

