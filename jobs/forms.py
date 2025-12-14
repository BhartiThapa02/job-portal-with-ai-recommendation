from django import forms
from .models import Job


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'requirements', 'skills_required',
            'location', 'work_mode', 'job_type', 'experience_level',
            'salary_min', 'salary_max', 'salary_currency', 'deadline',
            'is_featured'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 10}),
            'requirements': forms.Textarea(attrs={'rows': 10}),
            'deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'skills_required': forms.TextInput(attrs={'placeholder': 'Comma-separated skills'}),
        }
    
    def clean_skills_required(self):
        skills = self.cleaned_data.get('skills_required')
        if isinstance(skills, str):
            # Convert comma-separated string to list
            skills = [s.strip() for s in skills.split(',') if s.strip()]
        elif not skills:
            skills = []
        return skills

