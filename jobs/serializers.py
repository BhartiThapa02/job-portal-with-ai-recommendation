from rest_framework import serializers
from .models import Job
from companies.serializers import CompanySerializer


class JobSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    
    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['company', 'views', 'application_count', 'created_at', 'updated_at']

