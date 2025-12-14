"""
Utility functions for job recommendations and matching
"""
from django.db.models import Q, Count
from django.utils import timezone
from .models import Job, JobRecommendation
from accounts.models import JobSeekerProfile


def calculate_job_match_score(user, job):
    """
    Calculate how well a job matches a user's profile
    Returns a score between 0 and 100
    """
    score = 0.0
    reasons = []
    
    try:
        profile = user.job_seeker_profile
    except JobSeekerProfile.DoesNotExist:
        return 0.0, ["Profile not complete"]
    
    # Skill matching (40% weight)
    if profile.skills and job.skills_required:
        user_skills = [s.lower() for s in profile.skills]
        job_skills = [s.lower() for s in job.skills_required]
        
        matching_skills = set(user_skills) & set(job_skills)
        if job_skills:
            skill_match_ratio = len(matching_skills) / len(job_skills)
            score += skill_match_ratio * 40
            if matching_skills:
                reasons.append(f"Matches {len(matching_skills)} required skills")
    
    # Experience level matching (20% weight)
    experience_map = {
        'entry': 0,
        'mid': 3,
        'senior': 7,
        'executive': 10
    }
    
    user_experience = profile.experience_years or 0
    job_experience_min = experience_map.get(job.experience_level, 0)
    
    if user_experience >= job_experience_min:
        score += 20
        reasons.append("Experience level matches")
    elif user_experience >= job_experience_min - 2:
        score += 10
        reasons.append("Experience level close")
    
    # Location matching (15% weight)
    if profile.location and job.location:
        user_location = profile.location.lower()
        job_location = job.location.lower()
        
        # Check if locations match (simple check)
        if user_location in job_location or job_location in user_location:
            score += 15
            reasons.append("Location matches")
        elif job.work_mode == 'remote':
            score += 15
            reasons.append("Remote position")
    
    # Work mode preference (10% weight)
    # Assuming user prefers remote if not specified
    if job.work_mode == 'remote':
        score += 10
        reasons.append("Remote work available")
    
    # Education matching (10% weight)
    if profile.education and len(profile.education) > 0:
        score += 10
        reasons.append("Education background available")
    
    # Resume keywords matching (5% weight)
    if profile.resume:
        score += 5
        reasons.append("Resume available")
    
    return min(score, 100.0), reasons


def generate_job_recommendations(user, limit=20):
    """
    Generate job recommendations for a user
    """
    if not user.is_job_seeker:
        return []
    
    # Get all active jobs (exclude expired jobs)
    now = timezone.now()
    active_jobs = Job.objects.filter(is_active=True).filter(
        Q(deadline__isnull=True) | Q(deadline__gt=now)
    )
    
    # Calculate scores for each job
    recommendations = []
    for job in active_jobs:
        # Check if user already applied
        from applications.models import Application
        if Application.objects.filter(user=user, job=job).exists():
            continue
        
        score, reasons = calculate_job_match_score(user, job)
        
        if score > 30:  # Only recommend jobs with score > 30
            recommendations.append({
                'job': job,
                'score': score,
                'reasons': reasons
            })
    
    # Sort by score
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    # Save to database
    for rec in recommendations[:limit]:
        JobRecommendation.objects.update_or_create(
            user=user,
            job=rec['job'],
            defaults={
                'score': rec['score'],
                'reason': ', '.join(rec['reasons'])
            }
        )
    
    return recommendations[:limit]


def get_job_recommendations_for_user(user, limit=20):
    """
    Get cached recommendations or generate new ones
    """
    # Check if we have recent recommendations (less than 24 hours old)
    from django.utils import timezone
    from datetime import timedelta
    
    recent_recommendations = JobRecommendation.objects.filter(
        user=user,
        created_at__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-score')[:limit]
    
    if recent_recommendations.exists():
        return recent_recommendations
    
    # Generate new recommendations
    generate_job_recommendations(user, limit)
    
    return JobRecommendation.objects.filter(user=user).order_by('-score')[:limit]

