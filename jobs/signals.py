from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from .models import Job


@receiver(post_save, sender=Job)
def notify_job_seekers_on_new_job(sender, instance: Job, created: bool, **kwargs):
    """
    Send an email notification to all job seekers when a new job is posted.
    For safety, this is fail-silent and will use DEFAULT_FROM_EMAIL or a fallback.
    """
    if not created:
        return

    # Fetch verified job seekers
    recipients = list(
        User.objects.filter(user_type='job_seeker', is_email_verified=True)
        .values_list('email', flat=True)
    )
    if not recipients:
        return

    subject = f"New job posted: {instance.title}"
    job_url = f"{getattr(settings, 'SITE_URL', '').rstrip('/')}/jobs/{instance.id}/"
    if not getattr(settings, 'SITE_URL', None):
        # Fallback relative link if SITE_URL is not set
        job_url = f"/jobs/{instance.id}/"

    message = (
        f"Hi there!\n\n"
        f"A new job has just been posted:\n"
        f"Title: {instance.title}\n"
        f"Company: {instance.company.name}\n"
        f"Location: {instance.location}\n"
        f"Type: {instance.get_job_type_display()}\n\n"
        f"View and apply here: {job_url}\n\n"
        f"Happy job hunting!\n"
        f"- Job Portal Team"
    )

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com')

    # Fail silently to avoid breaking job creation if email errors occur
    send_mail(
        subject,
        message,
        from_email,
        recipients,
        fail_silently=True,
    )

