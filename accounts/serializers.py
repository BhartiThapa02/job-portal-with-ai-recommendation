from rest_framework import serializers
from .models import User, JobSeekerProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'user_type', 'phone', 'is_email_verified', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class JobSeekerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = JobSeekerProfile
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']

