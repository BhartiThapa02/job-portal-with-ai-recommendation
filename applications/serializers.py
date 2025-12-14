from rest_framework import serializers
from .models import Application, ApplicationMessage
from jobs.serializers import JobSerializer
from accounts.serializers import UserSerializer


class ApplicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    job = JobSerializer(read_only=True)
    
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ['user', 'applied_at', 'updated_at']


class ApplicationMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = ApplicationMessage
        fields = '__all__'
        read_only_fields = ['sender', 'created_at']

