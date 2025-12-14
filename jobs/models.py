from django.db import models
from django.conf import settings
from django.utils import timezone


class Job(models.Model):
    """Job Posting Model"""
    WORK_MODE_CHOICES = [
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('onsite', 'Onsite'),
    ]
    
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
        ('executive', 'Executive'),
    ]
    
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='jobs')
    title = models.CharField(max_length=200)
    description = models.TextField()
    requirements = models.TextField()
    skills_required = models.JSONField(default=list, blank=True)  # ["Python", "Django", "React"]
    location = models.CharField(max_length=200)
    work_mode = models.CharField(max_length=20, choices=WORK_MODE_CHOICES, default='onsite')
    job_type = models.CharField(max_length=20, choices=JOB_TYPE_CHOICES, default='full_time')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, default='mid')
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    salary_currency = models.CharField(max_length=10, default='USD')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    application_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
    
    def __str__(self):
        return f"{self.title} - {self.company.name}"
    
    @property
    def is_expired(self):
        if self.deadline:
            return timezone.now() > self.deadline
        return False
    
    def increment_views(self):
        self.views += 1
        self.save(update_fields=['views'])


class JobView(models.Model):
    """Track job views"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_views')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Job View'
        verbose_name_plural = 'Job Views'
        unique_together = ['job', 'user', 'ip_address']


class JobRecommendation(models.Model):
    """Job Recommendations (rule-based matching algorithm)"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_recommendations')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='recommendations')
    score = models.FloatField(default=0.0)  # Recommendation score
    reason = models.TextField(blank=True)  # Why this job was recommended
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-score', '-created_at']
        unique_together = ['user', 'job']

