"""
OAuth Login Views (Google OAuth)
Note: Requires django-allauth to be installed and configured
"""
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from .models import User, JobSeekerProfile


def oauth_callback(request):
    """
    Handle OAuth callback
    This is a placeholder - actual implementation depends on django-allauth
    """
    # When django-allauth is installed, this will be handled automatically
    # via the allauth URLs
    
    # For now, redirect to login
    messages.info(request, 'OAuth login is not yet configured. Please use regular login.')
    return redirect('accounts:login')


def google_login(request):
    """
    Initiate Google OAuth login
    Placeholder for when django-allauth is configured
    """
    # When django-allauth is installed:
    # from allauth.socialaccount.providers.google.views import oauth2_login
    # return oauth2_login(request)
    
    messages.info(request, 'Google OAuth is not yet configured. Please use regular login.')
    return redirect('accounts:login')

