from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Job, JobView, JobRecommendation
from applications.models import Application
from accounts.models import SavedJob


def home(request):
    """Homepage with recent jobs"""
    # Exclude expired jobs (deadline has passed)
    now = timezone.now()
    recent_jobs = Job.objects.filter(
        is_active=True
    ).filter(
        Q(deadline__isnull=True) | Q(deadline__gt=now)
    ).order_by('-created_at')[:10]
    featured_jobs = Job.objects.filter(
        is_active=True, 
        is_featured=True
    ).filter(
        Q(deadline__isnull=True) | Q(deadline__gt=now)
    ).order_by('-created_at')[:6]
    
    context = {
        'recent_jobs': recent_jobs,
        'featured_jobs': featured_jobs,
    }
    return render(request, 'jobs/home.html', context)


def search_jobs(request):
    """Job search with filters"""
    # Exclude expired jobs (deadline has passed)
    now = timezone.now()
    jobs = Job.objects.filter(is_active=True).filter(
        Q(deadline__isnull=True) | Q(deadline__gt=now)
    )
    
    # Search query
    query = request.GET.get('q', '')
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(company__name__icontains=query) |
            Q(skills_required__icontains=query)
        )
    
    # Filters
    location = request.GET.get('location')
    if location:
        # More flexible location matching - split by comma and search for any part
        location_parts = [part.strip() for part in location.split(',')]
        location_query = Q()
        for part in location_parts:
            if part:
                location_query |= Q(location__icontains=part)
        if location_query:
            jobs = jobs.filter(location_query)
    
    work_mode = request.GET.get('work_mode')
    if work_mode:
        jobs = jobs.filter(work_mode=work_mode)
    
    job_type = request.GET.get('job_type')
    if job_type:
        jobs = jobs.filter(job_type=job_type)
    
    experience_level = request.GET.get('experience_level')
    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)
    
    salary_min = request.GET.get('salary_min')
    if salary_min:
        jobs = jobs.filter(salary_max__gte=salary_min)
    
    # Pagination
    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'jobs': page_obj,
        'query': query,
        'filters': {
            'location': location,
            'work_mode': work_mode,
            'job_type': job_type,
            'experience_level': experience_level,
            'salary_min': salary_min,
        }
    }
    return render(request, 'jobs/search.html', context)


def job_detail(request, job_id):
    """Job detail page"""
    # Exclude expired jobs (deadline has passed)
    now = timezone.now()
    job = get_object_or_404(
        Job, 
        id=job_id, 
        is_active=True
    )
    # Check if job is expired
    if job.deadline and job.deadline <= now:
        messages.warning(request, 'This job posting has expired.')
        return redirect('jobs:home')
    
    # Track view
    if request.user.is_authenticated:
        JobView.objects.get_or_create(job=job, user=request.user)
    else:
        ip_address = request.META.get('REMOTE_ADDR')
        JobView.objects.get_or_create(job=job, ip_address=ip_address)
    
    job.increment_views()
    
    # Check if user already applied
    has_applied = False
    is_saved = False
    if request.user.is_authenticated:
        has_applied = Application.objects.filter(user=request.user, job=job).exists()
        is_saved = SavedJob.objects.filter(user=request.user, job=job).exists()
    
    # Related jobs - exclude expired jobs
    now = timezone.now()
    related_jobs = Job.objects.filter(
        is_active=True,
        skills_required__overlap=job.skills_required
    ).filter(
        Q(deadline__isnull=True) | Q(deadline__gt=now)
    ).exclude(id=job.id)[:5]
    
    context = {
        'job': job,
        'has_applied': has_applied,
        'is_saved': is_saved,
        'related_jobs': related_jobs,
    }
    return render(request, 'jobs/detail.html', context)


@login_required
def apply_job(request, job_id):
    """Apply to a job"""
    if not request.user.is_job_seeker:
        messages.error(request, 'Only job seekers can apply for jobs.')
        return redirect('jobs:detail', job_id=job_id)
    
    job = get_object_or_404(Job, id=job_id, is_active=True)
    
    # Check if job is expired
    if job.deadline and job.deadline <= timezone.now():
        messages.error(request, 'This job posting has expired and applications are no longer accepted.')
        return redirect('jobs:detail', job_id=job_id)
    
    # Check if already applied
    if Application.objects.filter(user=request.user, job=job).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('jobs:detail', job_id=job_id)
    
    # Check if user has resume
    try:
        profile = request.user.job_seeker_profile
        if not profile.resume:
            messages.warning(request, 'Please upload your resume before applying.')
            return redirect('accounts:update_profile')
    except:
        messages.warning(request, 'Please complete your profile before applying.')
        return redirect('accounts:update_profile')
    
    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '')
        application = Application.objects.create(
            user=request.user,
            job=job,
            cover_letter=cover_letter,
            status='applied'
        )
        
        # Create notification
        from notifications.models import Notification
        Notification.objects.create(
            user=request.user,
            title='Application Submitted',
            message=f'Your application for {job.title} has been submitted successfully.',
            notification_type='application_submitted'
        )
        
        messages.success(request, 'Application submitted successfully!')
        return redirect('applications:my_applications')
    
    return render(request, 'jobs/apply.html', {'job': job})


@login_required
def save_job(request, job_id):
    """Save/Unsave a job"""
    if not request.user.is_job_seeker:
        messages.error(request, 'Only job seekers can save jobs.')
        return redirect('jobs:detail', job_id=job_id)
    
    # Allow saving expired jobs (user might want to reference them)
    job = get_object_or_404(Job, id=job_id, is_active=True)
    saved_job, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    
    if created:
        messages.success(request, 'Job saved successfully!')
    else:
        saved_job.delete()
        messages.info(request, 'Job removed from saved jobs.')
    
    return redirect('jobs:detail', job_id=job_id)


@login_required
def saved_jobs(request):
    """View saved jobs"""
    if not request.user.is_job_seeker:
        return redirect('jobs:home')
    
    saved_jobs = SavedJob.objects.filter(user=request.user).order_by('-saved_at')
    return render(request, 'jobs/saved.html', {'saved_jobs': saved_jobs})


@login_required
def recommendations(request):
    """Job recommendations - AI-powered if resume available, otherwise rule-based"""
    if not request.user.is_job_seeker:
        return redirect('jobs:home')
    
    profile = None
    try:
        profile = request.user.job_seeker_profile
    except:
        pass
    
    recommendations_list = []
    use_ai = False
    
    # First, check if we have saved recommendations in database
    from .models import JobRecommendation
    from django.utils import timezone
    from datetime import timedelta
    
    # Check for recent recommendations (less than 7 days old)
    saved_recommendations_qs = JobRecommendation.objects.filter(
        user=request.user,
        created_at__gte=timezone.now() - timedelta(days=7)
    ).select_related('job', 'job__company').order_by('-score')
    
    # Check if we have any recommendations
    if saved_recommendations_qs.exists():
        # Check if they're AI recommendations (before slicing)
        ai_rec = saved_recommendations_qs.filter(reason__startswith='AI Match').first()
        use_ai = ai_rec is not None
        
        # Now slice the queryset
        saved_recommendations = saved_recommendations_qs[:20]
        
        # Convert to list format expected by template
        for rec in saved_recommendations:
            if use_ai and rec.reason and rec.reason.startswith('AI Match'):
                # Extract match percentage from reason (format: "AI Match: 85.3% similarity...")
                match_pct = rec.score  # Score is already 0-100 scale
                recommendations_list.append({
                    'job': rec.job,
                    'score': rec.score,
                    'match_percentage': match_pct,  # Use score as match percentage
                    'reason': rec.reason
                })
            else:
                recommendations_list.append({
                    'job': rec.job,
                    'score': rec.score,
                    'reason': rec.reason or ''
                })
    else:
        # No saved recommendations, generate new ones
        # Try AI recommendations first if user has a resume
        if profile and profile.resume:
            try:
                from .ai_recommender import recommend_jobs_from_resume
                ai_recommendations = recommend_jobs_from_resume(profile.resume, request.user, top_k=20)
                if ai_recommendations:
                    use_ai = True
                    recommendations_list = ai_recommendations
            except ImportError:
                # AI dependencies not installed
                pass
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"AI recommendation error: {e}")
        
        # Fallback to rule-based recommendations
        if not recommendations_list:
            from .utils import get_job_recommendations_for_user
            rule_based = get_job_recommendations_for_user(request.user, limit=20)
            # Convert JobRecommendation objects to dict format
            for rec in rule_based:
                recommendations_list.append({
                    'job': rec.job,
                    'score': rec.score,
                    'reason': rec.reason or ''
                })
    
    context = {
        'recommendations': recommendations_list,
        'use_ai': use_ai,
        'has_resume': profile.resume if profile else False
    }
    
    return render(request, 'jobs/recommendations.html', context)

