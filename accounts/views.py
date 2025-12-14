from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import select_template
from django.template import TemplateDoesNotExist
from django.template import engines
from django.http import HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from datetime import timedelta
from .models import User, JobSeekerProfile, PasswordResetToken, EmailVerificationToken
from .forms import UserRegistrationForm, JobSeekerProfileForm
import secrets


@ensure_csrf_cookie
def register(request):
    if request.method == 'POST':
        # Use request.POST directly - CSRF token is validated by middleware
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Save the user (password is set in form.save())
                user = form.save(commit=False)
                user.is_email_verified = False
                user.user_type = form.cleaned_data.get('user_type', 'job_seeker')
                user.save()
                
                # Create verification token
                token = secrets.token_urlsafe(32)
                expires_at = timezone.now() + timedelta(days=1)
                EmailVerificationToken.objects.create(
                    user=user,
                    token=token,
                    expires_at=expires_at
                )
                
                # Send verification email
                try:
                    verification_link = request.build_absolute_uri(f'/accounts/verify-email/{token}/')
                    send_mail(
                        'Verify Your Email - Job Portal',
                        f'Click the link to verify your email: {verification_link}',
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Failed to send verification email: {e}")
                
                messages.success(request, 'Registration successful! Please check your email to verify your account.')
                return redirect('jobs:home')
                
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
                print(f"Registration error: {e}")
        else:
            # Form validation errors
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    # Render the registration form
    return render(request, 'accounts/register.html', {'form': form})


@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'Please provide both email and password.')
            return redirect('jobs:home')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_banned:
                messages.error(request, 'Your account has been banned. Please contact support.')
                return redirect('jobs:home')
            if user.is_suspended:
                messages.error(request, 'Your account has been suspended. Please contact support.')
                return redirect('jobs:home')
            if user.is_employer and not user.is_approved:
                messages.warning(request, 'Your employer account is pending approval.')
                return redirect('jobs:home')
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.email}!')
            
            # Redirect to next page if specified (from session or parameter)
            next_url = request.GET.get('next') or request.POST.get('next') or request.session.pop('login_next', None)
            if next_url:
                return redirect(next_url)
            
            if user.is_employer:
                return redirect('companies:dashboard')
            else:
                return redirect('jobs:home')
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('jobs:home')
    
    # For GET requests, redirect to home (login handled via modal)
    # If next parameter exists, store it in session
    if request.GET.get('next'):
        request.session['login_next'] = request.GET.get('next')
    
    return redirect('jobs:home')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('jobs:home')


def verify_email(request, token):
    """Verify email with token"""
    try:
        verification_token = EmailVerificationToken.objects.get(
            token=token,
            is_used=False
        )
        
        if not verification_token.is_valid():
            messages.error(request, 'Verification link has expired. Please request a new one.')
            return redirect('jobs:home')
        
        user = verification_token.user
        user.is_email_verified = True
        user.save()
        
        verification_token.is_used = True
        verification_token.save()
        
        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('jobs:home')
        
    except EmailVerificationToken.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('jobs:home')


def resend_verification(request):
    """Resend email verification"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_email_verified:
                messages.info(request, 'Your email is already verified.')
                return redirect('jobs:home')
            
            # Invalidate old tokens
            EmailVerificationToken.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Create new token
            token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(days=1)
            EmailVerificationToken.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )
            
            # Send verification email
            try:
                verification_link = request.build_absolute_uri(f'/accounts/verify-email/{token}/')
                send_mail(
                    'Verify Your Email - Job Portal',
                    f'Click the link to verify your email: {verification_link}',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                messages.success(request, 'Verification email sent! Please check your inbox.')
            except Exception as e:
                messages.error(request, 'Failed to send verification email. Please try again later.')
                print(f"Email error: {e}")
                
        except User.DoesNotExist:
            # Don't reveal if user exists for security
            messages.success(request, 'If an account exists with this email, a verification link has been sent.')
    
    return redirect('jobs:home')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if not email:
            messages.error(request, 'Please provide an email address.')
            return render(request, 'accounts/forgot_password.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Invalidate old tokens
            PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Create new token
            token = secrets.token_urlsafe(32)
            expires_at = timezone.now() + timedelta(hours=1)
            PasswordResetToken.objects.create(
                user=user,
                token=token,
                expires_at=expires_at
            )
            
            # Send reset email
            try:
                reset_link = request.build_absolute_uri(f'/accounts/reset-password/{token}/')
                send_mail(
                    'Reset Your Password - Job Portal',
                    f'Click the link to reset your password: {reset_link}\n\nThis link will expire in 1 hour.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Failed to send reset email: {e}")
            
            messages.success(request, 'Password reset link sent to your email.')
            
        except User.DoesNotExist:
            # Don't reveal if user exists for security
            messages.success(request, 'If an account exists with this email, a password reset link has been sent.')
    
    return render(request, 'accounts/forgot_password.html')


def reset_password(request, token):
    try:
        reset_token = PasswordResetToken.objects.get(
            token=token,
            is_used=False
        )
        
        if not reset_token.is_valid():
            messages.error(request, 'Password reset link has expired. Please request a new one.')
            return redirect('accounts:forgot_password')
        
        if request.method == 'POST':
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            if not password or not password_confirm:
                messages.error(request, 'Please fill in all fields.')
                return render(request, 'accounts/reset_password.html', {'token': token})
            
            if password != password_confirm:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/reset_password.html', {'token': token})
            
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'accounts/reset_password.html', {'token': token})
            
            # Reset password
            user = reset_token.user
            user.set_password(password)
            user.save()
            
            # Mark token as used
            reset_token.is_used = True
            reset_token.save()
            
            messages.success(request, 'Password reset successful! Please login with your new password.')
            return redirect('jobs:home')
        
        return render(request, 'accounts/reset_password.html', {'token': token})
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('accounts:forgot_password')


@login_required
def profile(request):
    if request.user.is_job_seeker:
        try:
            profile = request.user.job_seeker_profile
        except JobSeekerProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = JobSeekerProfile.objects.create(user=request.user)
        
        return render(request, 'accounts/profile.html', {'profile': profile})
    else:
        return redirect('companies:profile')


@login_required
def update_profile(request):
    if not request.user.is_job_seeker:
        messages.error(request, 'Only job seekers can update this profile.')
        return redirect('companies:profile')
    
    try:
        profile = request.user.job_seeker_profile
    except JobSeekerProfile.DoesNotExist:
        profile = JobSeekerProfile(user=request.user)
    
    if request.method == 'POST':
        # Validate file uploads before form processing
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            # Check file size (max 5MB)
            if profile_picture.size > 5 * 1024 * 1024:
                messages.error(request, 'Profile picture file size must be less than 5MB.')
                form = JobSeekerProfileForm(instance=profile)
                return render(request, 'accounts/update_profile.html', {'form': form, 'profile': profile})
            # Check file type
            if not profile_picture.content_type.startswith('image/'):
                messages.error(request, 'Profile picture must be an image file.')
                form = JobSeekerProfileForm(instance=profile)
                return render(request, 'accounts/update_profile.html', {'form': form, 'profile': profile})
        
        if 'resume' in request.FILES:
            resume_file = request.FILES['resume']
            # Check file size (max 10MB)
            if resume_file.size > 10 * 1024 * 1024:
                messages.error(request, 'Resume file size must be less than 10MB.')
                form = JobSeekerProfileForm(instance=profile)
                return render(request, 'accounts/update_profile.html', {'form': form, 'profile': profile})
            # Check file type
            allowed_types = ['application/pdf', 'application/msword', 
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            if resume_file.content_type not in allowed_types:
                messages.error(request, 'Resume must be a PDF or DOC/DOCX file.')
                form = JobSeekerProfileForm(instance=profile)
                return render(request, 'accounts/update_profile.html', {'form': form, 'profile': profile})
        
        form = JobSeekerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            try:
                resume_uploaded = 'resume' in request.FILES
                old_resume = profile.resume if profile.pk else None
                
                form.save()
                
                # If resume was uploaded, generate AI recommendations
                if resume_uploaded and profile.resume:
                    try:
                        from jobs.ai_recommender import recommend_jobs_from_resume
                        ai_recommendations = recommend_jobs_from_resume(profile.resume, request.user, top_k=10)
                        if ai_recommendations:
                            messages.success(request, f'Profile updated! Found {len(ai_recommendations)} AI-powered job recommendations based on your resume.')
                        else:
                            messages.success(request, 'Profile updated successfully!')
                    except Exception as e:
                        # If AI recommendation fails, still show success for profile update
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.error(f"AI recommendation error: {e}")
                        messages.success(request, 'Profile updated successfully! (AI recommendations temporarily unavailable)')
                else:
                    messages.success(request, 'Profile updated successfully!')
                
                return redirect('accounts:profile')
            except Exception as e:
                messages.error(request, f'Error saving profile: {str(e)}')
        else:
            # Display form errors
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            if error_messages:
                messages.error(request, 'Please correct the errors below: ' + ' | '.join(error_messages))
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        form = JobSeekerProfileForm(instance=profile)
    
    return render(request, 'accounts/update_profile.html', {'form': form, 'profile': profile})


@login_required
def change_password(request):
    """Change password for logged-in user"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not all([old_password, new_password, confirm_password]):
            messages.error(request, 'Please fill in all fields.')
            return render(request, 'accounts/change_password.html')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Your old password is incorrect.')
            return render(request, 'accounts/change_password.html')
        
        if new_password != confirm_password:
            messages.error(request, 'New passwords do not match.')
            return render(request, 'accounts/change_password.html')
        
        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'accounts/change_password.html')
        
        # Change password
        request.user.set_password(new_password)
        request.user.save()
        
        # Keep user logged in after password change
        update_session_auth_hash(request, request.user)
        
        messages.success(request, 'Password changed successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/change_password.html')