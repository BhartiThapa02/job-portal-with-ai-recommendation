from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, JobSeekerProfile


class UserRegistrationForm(forms.ModelForm):
    """Custom user registration form"""
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        }),
        help_text='Password must be at least 8 characters'
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )
    user_type = forms.ChoiceField(
        choices=[('job_seeker', 'Job Seeker'), ('employer', 'Employer')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'user_type']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username (optional)'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone number (optional)'
            }),
        }
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email
    
    def clean_username(self):
        """Auto-generate username if not provided"""
        username = self.cleaned_data.get('username')
        if not username:
            # Will be generated from email in the view
            return None
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username
    
    def clean_password2(self):
        """Validate passwords match"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('Passwords do not match.')
            if len(password1) < 8:
                raise ValidationError('Password must be at least 8 characters long.')
        return password2

    def clean(self):
        """
        Ensure a unified password key exists.
        Some code paths may look for `cleaned_data['password']`; we mirror
        password1 there to avoid KeyError while keeping validation intact.
        """
        cleaned_data = super().clean()
        if cleaned_data.get('password1'):
            cleaned_data['password'] = cleaned_data.get('password1')
        return cleaned_data
    
    def save(self, commit=True):
        """Save user with hashed password"""
        user = super().save(commit=False)
        
        # Generate username from email if not provided
        if not user.username:
            email_username = user.email.split('@')[0]
            base_username = email_username
            counter = 1
            while User.objects.filter(username=email_username).exists():
                email_username = f"{base_username}{counter}"
                counter += 1
            user.username = email_username
        
        # Set password - THIS IS THE KEY FIX
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        
        if commit:
            user.save()
        return user


class JobSeekerProfileForm(forms.ModelForm):
    """Job seeker profile form"""
    class Meta:
        model = JobSeekerProfile
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'profile_picture', 'resume', 'bio', 'location',
            'linkedin_url', 'github_url', 'portfolio_url',
            'skills', 'experience_years', 'education'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('male', 'Male'),
                ('female', 'Female'),
                ('other', 'Other'),
            ]),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control'}),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter skills separated by commas'
            }),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'education': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'One education item per line or JSON'
            }),
        }