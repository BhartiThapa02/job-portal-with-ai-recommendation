"""
Admin Analytics and Dashboard Views
"""
from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, JobSeekerProfile
from companies.models import Company
from jobs.models import Job, JobView
from applications.models import Application
from notifications.models import Notification
from .models import Analytics


@staff_member_required
def admin_analytics(request):
    """Admin Analytics Dashboard"""
    
    # User Statistics
    total_users = User.objects.count()
    total_job_seekers = User.objects.filter(user_type='job_seeker').count()
    total_employers = User.objects.filter(user_type='employer').count()
    verified_users = User.objects.filter(is_email_verified=True).count()
    approved_employers = User.objects.filter(user_type='employer', is_approved=True).count()
    pending_employers = User.objects.filter(user_type='employer', is_approved=False).count()
    suspended_users = User.objects.filter(is_suspended=True).count()
    banned_users = User.objects.filter(is_banned=True).count()
    
    # Job Statistics
    total_jobs = Job.objects.count()
    active_jobs = Job.objects.filter(is_active=True).count()
    inactive_jobs = Job.objects.filter(is_active=False).count()
    featured_jobs = Job.objects.filter(is_featured=True).count()
    total_job_views = JobView.objects.count()
    
    # Application Statistics
    total_applications = Application.objects.count()
    applications_by_status = Application.objects.values('status').annotate(count=Count('id'))
    
    # Company Statistics
    total_companies = Company.objects.count()
    verified_companies = Company.objects.filter(is_verified=True).count()
    
    # Recent Activity (Last 7 days)
    seven_days_ago = timezone.now() - timedelta(days=7)
    recent_users = User.objects.filter(created_at__gte=seven_days_ago).count()
    recent_jobs = Job.objects.filter(created_at__gte=seven_days_ago).count()
    recent_applications = Application.objects.filter(applied_at__gte=seven_days_ago).count()
    
    # Top Companies by Job Count
    top_companies = Company.objects.annotate(
        job_count=Count('jobs')
    ).order_by('-job_count')[:10]
    
    # Most Viewed Jobs
    most_viewed_jobs = Job.objects.order_by('-views')[:10]
    
    # Jobs by Work Mode
    jobs_by_work_mode = Job.objects.values('work_mode').annotate(count=Count('id'))
    
    # Jobs by Type
    jobs_by_type = Job.objects.values('job_type').annotate(count=Count('id'))
    
    # User Growth (Last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    user_growth = User.objects.filter(created_at__gte=thirty_days_ago).count()
    
    context = {
        # User Stats
        'total_users': total_users,
        'total_job_seekers': total_job_seekers,
        'total_employers': total_employers,
        'verified_users': verified_users,
        'approved_employers': approved_employers,
        'pending_employers': pending_employers,
        'suspended_users': suspended_users,
        'banned_users': banned_users,
        
        # Job Stats
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'inactive_jobs': inactive_jobs,
        'featured_jobs': featured_jobs,
        'total_job_views': total_job_views,
        
        # Application Stats
        'total_applications': total_applications,
        'applications_by_status': applications_by_status,
        
        # Company Stats
        'total_companies': total_companies,
        'verified_companies': verified_companies,
        
        # Recent Activity
        'recent_users': recent_users,
        'recent_jobs': recent_jobs,
        'recent_applications': recent_applications,
        
        # Top Lists
        'top_companies': top_companies,
        'most_viewed_jobs': most_viewed_jobs,
        
        # Breakdowns
        'jobs_by_work_mode': jobs_by_work_mode,
        'jobs_by_type': jobs_by_type,
        'user_growth': user_growth,
    }
    
    return render(request, 'admin/analytics.html', context)


@staff_member_required
def update_analytics(request):
    """Update analytics data (can be called via cron)"""
    from jobs.models import Job
    from applications.models import Application
    
    today = timezone.now().date()
    
    analytics, created = Analytics.objects.get_or_create(date=today)
    
    analytics.total_users = User.objects.count()
    analytics.total_job_seekers = User.objects.filter(user_type='job_seeker').count()
    analytics.total_employers = User.objects.filter(user_type='employer').count()
    analytics.total_jobs = Job.objects.count()
    analytics.total_applications = Application.objects.count()
    analytics.active_jobs = Job.objects.filter(is_active=True).count()
    
    analytics.save()
    
    messages.success(request, 'Analytics updated successfully!')
    return redirect('core:admin_analytics')

