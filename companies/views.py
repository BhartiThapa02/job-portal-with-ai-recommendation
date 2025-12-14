from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from .models import Company
from jobs.models import Job
from applications.models import Application


@login_required
def dashboard(request):
    if not request.user.is_employer:
        messages.error(request, 'Only employers can access the dashboard.')
        return redirect('jobs:home')
    
    try:
        company = request.user.company
    except Company.DoesNotExist:
        messages.info(request, 'Please complete your company profile to access the dashboard.')
        return redirect('companies:update_profile')
    
    # Dashboard statistics
    total_jobs = Job.objects.filter(company=company).count()
    total_applicants = Application.objects.filter(job__company=company).count()
    pending_applications = Application.objects.filter(job__company=company, status='applied').count()
    shortlisted = Application.objects.filter(job__company=company, status='shortlisted').count()
    interviews = Application.objects.filter(job__company=company, status='interview_scheduled').count()
    
    # Recent applications
    recent_applications = Application.objects.filter(job__company=company).order_by('-applied_at')[:10]
    
    # Job engagement stats
    jobs_with_stats = Job.objects.filter(company=company).annotate(
        view_count=Count('job_views'),
        applicant_count=Count('applications')
    ).order_by('-created_at')[:5]
    
    context = {
        'company': company,
        'total_jobs': total_jobs,
        'total_applicants': total_applicants,
        'pending_applications': pending_applications,
        'shortlisted': shortlisted,
        'interviews': interviews,
        'recent_applications': recent_applications,
        'jobs_with_stats': jobs_with_stats,
    }
    
    return render(request, 'companies/dashboard.html', context)


@login_required
def company_profile(request):
    if not request.user.is_employer:
        return redirect('jobs:home')
    
    try:
        company = request.user.company
    except Company.DoesNotExist:
        company = None
    
    return render(request, 'companies/profile.html', {'company': company})


@login_required
def update_company_profile(request):
    if not request.user.is_employer:
        return redirect('jobs:home')
    
    try:
        company = request.user.company
    except Company.DoesNotExist:
        company = Company(user=request.user)
    
    if request.method == 'POST':
        # Validate required fields
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Company name is required.')
            return render(request, 'companies/update_profile.html', {'company': company})
        
        company.name = name
        company.website = request.POST.get('website', '').strip()
        company.about = request.POST.get('about', '').strip()
        company.location = request.POST.get('location', '').strip()
        company.team_size = request.POST.get('team_size', '')
        
        founded_year = request.POST.get('founded_year')
        if founded_year:
            try:
                company.founded_year = int(founded_year)
            except ValueError:
                messages.error(request, 'Invalid founded year.')
                return render(request, 'companies/update_profile.html', {'company': company})
        
        # Validate and save logo
        if 'logo' in request.FILES:
            logo_file = request.FILES['logo']
            # Check file size (max 5MB)
            if logo_file.size > 5 * 1024 * 1024:
                messages.error(request, 'Logo file size must be less than 5MB.')
                return render(request, 'companies/update_profile.html', {'company': company})
            # Check file type
            if not logo_file.content_type.startswith('image/'):
                messages.error(request, 'Logo must be an image file.')
                return render(request, 'companies/update_profile.html', {'company': company})
            company.logo = logo_file
        
        # Validate and save banner
        if 'banner' in request.FILES:
            banner_file = request.FILES['banner']
            # Check file size (max 10MB)
            if banner_file.size > 10 * 1024 * 1024:
                messages.error(request, 'Banner file size must be less than 10MB.')
                return render(request, 'companies/update_profile.html', {'company': company})
            # Check file type
            if not banner_file.content_type.startswith('image/'):
                messages.error(request, 'Banner must be an image file.')
                return render(request, 'companies/update_profile.html', {'company': company})
            company.banner = banner_file
        
        try:
            company.save()
            messages.success(request, 'Company profile updated successfully!')
            return redirect('companies:profile')
        except Exception as e:
            messages.error(request, f'Error saving profile: {str(e)}')
            return render(request, 'companies/update_profile.html', {'company': company})
    
    return render(request, 'companies/update_profile.html', {'company': company})


@login_required
def company_jobs(request):
    if not request.user.is_employer:
        return redirect('jobs:home')
    
    try:
        company = request.user.company
    except Company.DoesNotExist:
        messages.warning(request, 'Please complete your company profile first.')
        return redirect('companies:profile')
    
    jobs = Job.objects.filter(company=company).order_by('-created_at')
    return render(request, 'companies/jobs.html', {'jobs': jobs})


@login_required
def create_job(request):
    if not request.user.is_employer:
        return redirect('jobs:home')
    
    try:
        company = request.user.company
    except Company.DoesNotExist:
        messages.warning(request, 'Please complete your company profile first.')
        return redirect('companies:profile')
    
    if request.method == 'POST':
        from jobs.forms import JobForm
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = company
            job.save()
            messages.success(request, 'Job posted successfully!')
            return redirect('companies:jobs')
    else:
        from jobs.forms import JobForm
        form = JobForm()
    
    return render(request, 'companies/create_job.html', {'form': form})


@login_required
def edit_job(request, job_id):
    if not request.user.is_employer:
        return redirect('jobs:home')
    
    job = get_object_or_404(Job, id=job_id, company=request.user.company)
    
    if request.method == 'POST':
        from jobs.forms import JobForm
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job updated successfully!')
            return redirect('companies:jobs')
    else:
        from jobs.forms import JobForm
        form = JobForm(instance=job)
    
    return render(request, 'companies/edit_job.html', {'form': form, 'job': job})


@login_required
def delete_job(request, job_id):
    if not request.user.is_employer:
        return redirect('jobs:home')
    
    job = get_object_or_404(Job, id=job_id, company=request.user.company)
    if request.method == 'POST':
        job.delete()
        messages.success(request, 'Job deleted successfully!')
        return redirect('companies:jobs')
    
    return render(request, 'companies/delete_job.html', {'job': job})


@login_required
def applicants(request):
    if not request.user.is_employer:
        return redirect('jobs:home')
    
    company = request.user.company
    applications = Application.objects.filter(job__company=company).order_by('-applied_at')
    
    # Filters
    status_filter = request.GET.get('status')
    job_filter = request.GET.get('job')
    skill_filter = request.GET.get('skill')
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    if job_filter:
        applications = applications.filter(job_id=job_filter)
    if skill_filter:
        applications = applications.filter(user__job_seeker_profile__skills__icontains=skill_filter)
    
    context = {
        'applications': applications,
        'jobs': Job.objects.filter(company=company),
    }
    
    return render(request, 'companies/applicants.html', context)


@login_required
def application_detail(request, application_id):
    if not request.user.is_employer:
        return redirect('jobs:home')
    
    application = get_object_or_404(Application, id=application_id, job__company=request.user.company)
    return render(request, 'companies/application_detail.html', {'application': application})


@login_required
def update_application_status(request, application_id):
    if not request.user.is_employer:
        return redirect('jobs:home')
    
    application = get_object_or_404(Application, id=application_id, job__company=request.user.company)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        interview_date = request.POST.get('interview_date')
        interview_location = request.POST.get('interview_location')
        notes = request.POST.get('notes', '')
        
        if new_status in dict(Application.STATUS_CHOICES):
            application.status = new_status
            if interview_date:
                from django.utils.dateparse import parse_datetime
                application.interview_date = parse_datetime(interview_date)
            if interview_location:
                application.interview_location = interview_location
            if notes:
                application.notes = notes
            application.save()
            
            # Create notification
            from notifications.models import Notification
            Notification.objects.create(
                user=application.user,
                title='Application Status Updated',
                message=f'Your application for {application.job.title} has been {new_status}.',
                notification_type='application_update',
                link=f'/applications/{application_id}/'
            )
            
            # Special notification for interview scheduling
            if new_status == 'interview_scheduled' and interview_date:
                Notification.objects.create(
                    user=application.user,
                    title='Interview Scheduled',
                    message=f'Your interview for {application.job.title} has been scheduled.',
                    notification_type='interview_scheduled',
                    link=f'/applications/{application_id}/'
                )
            
            messages.success(request, 'Application status updated successfully!')
            return redirect('companies:application_detail', application_id=application_id)
    
    return redirect('companies:applicants')


@login_required
def message_candidate(request, application_id):
    """Send message to candidate"""
    if not request.user.is_employer:
        return redirect('jobs:home')
    
    application = get_object_or_404(Application, id=application_id, job__company=request.user.company)
    
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            from applications.models import ApplicationMessage
            ApplicationMessage.objects.create(
                application=application,
                sender=request.user,
                message=message_text
            )
            
            # Create notification for candidate
            from notifications.models import Notification
            Notification.objects.create(
                user=application.user,
                title='New Message',
                message=f'You have a new message regarding your application for {application.job.title}.',
                notification_type='message',
                link=f'/applications/{application_id}/'
            )
            
            messages.success(request, 'Message sent successfully!')
            return redirect('companies:application_detail', application_id=application_id)
    
    return redirect('companies:application_detail', application_id=application_id)


@login_required
def download_resume(request, application_id):
    """Download candidate's resume"""
    if not request.user.is_employer:
        return redirect('jobs:home')
    
    application = get_object_or_404(Application, id=application_id, job__company=request.user.company)
    
    try:
        profile = application.user.job_seeker_profile
        if profile.resume:
            from django.http import FileResponse
            return FileResponse(profile.resume.open(), as_attachment=True, filename=profile.resume.name)
        else:
            messages.warning(request, 'Candidate has not uploaded a resume.')
    except:
        messages.error(request, 'Resume not found.')
    
    return redirect('companies:application_detail', application_id=application_id)

