from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Application, ApplicationMessage
from notifications.models import Notification


@login_required
def my_applications(request):
    """View all user's applications"""
    if request.user.is_job_seeker:
        applications = Application.objects.filter(user=request.user).select_related('job', 'job__company').order_by('-applied_at')
        
        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter:
            applications = applications.filter(status=status_filter)
        
        context = {
            'applications': applications,
            'status_filter': status_filter,
        }
        return render(request, 'applications/my_applications.html', context)
    else:
        return redirect('companies:applicants')


@login_required
def application_detail(request, application_id):
    """Application detail view"""
    application = get_object_or_404(Application, id=application_id)
    
    # Check permissions
    if request.user.is_job_seeker and application.user != request.user:
        messages.error(request, 'You do not have permission to view this application.')
        return redirect('applications:my_applications')
    
    if request.user.is_employer and application.job.company.user != request.user:
        messages.error(request, 'You do not have permission to view this application.')
        return redirect('companies:applicants')
    
    # Get messages for this application
    application_messages = application.messages.all().order_by('created_at')
    
    context = {
        'application': application,
        'application_messages': application_messages,
    }
    return render(request, 'applications/detail.html', context)


@login_required
def view_application(request, application_id):
    """View application (for employers)"""
    if not request.user.is_employer:
        messages.error(request, 'Only employers can view applications.')
        return redirect('applications:my_applications')
    
    application = get_object_or_404(
        Application.objects.select_related('user', 'job', 'job__company'),
        id=application_id,
        job__company__user=request.user
    )
    
    # Get messages for this application
    application_messages = application.messages.all().order_by('created_at')
    
    context = {
        'application': application,
        'application_messages': application_messages,
    }
    return render(request, 'applications/view.html', context)


@login_required
def reply_message(request, application_id):
    """Reply to a message (for job seekers)"""
    if not request.user.is_job_seeker:
        messages.error(request, 'Only job seekers can reply to messages.')
        return redirect('applications:my_applications')
    
    application = get_object_or_404(Application, id=application_id, user=request.user)
    
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            # Create message
            ApplicationMessage.objects.create(
                application=application,
                sender=request.user,
                message=message_text
            )
            
            # Create notification for employer
            try:
                Notification.objects.create(
                    user=application.job.company.user,
                    title='New Message',
                    message=f'You have a new message from {request.user.email} regarding {application.job.title}.',
                    notification_type='message',
                    link=f'/companies/applicants/{application_id}/'
                )
            except Exception as e:
                # Log error but don't fail the message sending
                print(f"Failed to create notification: {e}")
            
            messages.success(request, 'Message sent successfully!')
        else:
            messages.error(request, 'Message cannot be empty.')
    else:
        messages.error(request, 'Invalid request method.')
    
    return redirect('applications:detail', application_id=application_id)


@login_required
def send_message(request, application_id):
    """Send a message (for employers)"""
    if not request.user.is_employer:
        messages.error(request, 'Only employers can send messages.')
        return redirect('applications:my_applications')
    
    application = get_object_or_404(
        Application,
        id=application_id,
        job__company__user=request.user
    )
    
    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            # Create message
            ApplicationMessage.objects.create(
                application=application,
                sender=request.user,
                message=message_text
            )
            
            # Create notification for job seeker
            try:
                Notification.objects.create(
                    user=application.user,
                    title='New Message from Employer',
                    message=f'You have a new message regarding your application for {application.job.title}.',
                    notification_type='message',
                    link=f'/applications/{application_id}/'
                )
            except Exception as e:
                print(f"Failed to create notification: {e}")
            
            messages.success(request, 'Message sent successfully!')
        else:
            messages.error(request, 'Message cannot be empty.')
    else:
        messages.error(request, 'Invalid request method.')
    
    return redirect('companies:view_application', application_id=application_id)


@login_required
def withdraw_application(request, application_id):
    """Withdraw an application"""
    if not request.user.is_job_seeker:
        messages.error(request, 'Only job seekers can withdraw applications.')
        return redirect('jobs:home')
    
    application = get_object_or_404(Application, id=application_id, user=request.user)
    
    if application.status in ['withdrawn', 'rejected', 'accepted']:
        messages.error(request, f'Cannot withdraw application with status: {application.get_status_display()}')
        return redirect('applications:my_applications')
    
    if request.method == 'POST':
        application.status = 'withdrawn'
        application.save()
        
        # Notify employer
        try:
            Notification.objects.create(
                user=application.job.company.user,
                title='Application Withdrawn',
                message=f'{request.user.email} has withdrawn their application for {application.job.title}.',
                notification_type='application',
                link=f'/companies/applicants/'
            )
        except Exception as e:
            print(f"Failed to create notification: {e}")
        
        messages.success(request, 'Application withdrawn successfully.')
        return redirect('applications:my_applications')
    
    return render(request, 'applications/withdraw_confirm.html', {'application': application})