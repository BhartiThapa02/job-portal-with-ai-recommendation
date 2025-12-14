from django.db import models
from django.conf import settings


class Company(models.Model):
    """Company/Employer Model"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='company')
    name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='company_banners/', blank=True, null=True)
    about = models.TextField(blank=True)
    industries = models.JSONField(default=list, blank=True)  # ["Technology", "Finance"]
    team_size = models.CharField(max_length=50, choices=[
        ('1-10', '1-10'),
        ('11-50', '11-50'),
        ('51-200', '51-200'),
        ('201-500', '201-500'),
        ('500+', '500+'),
    ], blank=True)
    location = models.CharField(max_length=200, blank=True)
    founded_year = models.IntegerField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
    
    def __str__(self):
        return self.name


class Recruiter(models.Model):
    """Recruiter/HR Model"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recruiter_profiles')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='recruiters')
    is_primary = models.BooleanField(default=False)  # Primary recruiter for the company
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Recruiter'
        verbose_name_plural = 'Recruiters'
    
    def __str__(self):
        return f"{self.user.email} - {self.company.name}"

