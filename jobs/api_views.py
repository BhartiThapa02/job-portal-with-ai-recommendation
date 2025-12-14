from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q
from django.utils import timezone
from .models import Job
from .serializers import JobSerializer
from applications.models import Application
from accounts.models import SavedJob


class JobViewSet(viewsets.ModelViewSet):
    # Exclude expired jobs (deadline has passed)
    now = timezone.now()
    queryset = Job.objects.filter(is_active=True).filter(
        Q(deadline__isnull=True) | Q(deadline__gt=now)
    )
    serializer_class = JobSerializer
    permission_classes = [AllowAny]
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        job = self.get_object()
        if not request.user.is_job_seeker:
            return Response({'error': 'Only job seekers can apply'}, status=status.HTTP_403_FORBIDDEN)
        
        if Application.objects.filter(user=request.user, job=job).exists():
            return Response({'error': 'Already applied'}, status=status.HTTP_400_BAD_REQUEST)
        
        application = Application.objects.create(
            user=request.user,
            job=job,
            status='applied'
        )
        return Response({'message': 'Application submitted'}, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post', 'delete'])
    def save(self, request, pk=None):
        job = self.get_object()
        if request.method == 'POST':
            SavedJob.objects.get_or_create(user=request.user, job=job)
            return Response({'message': 'Job saved'})
        else:
            SavedJob.objects.filter(user=request.user, job=job).delete()
            return Response({'message': 'Job unsaved'})


class JobSearchAPIView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Exclude expired jobs (deadline has passed)
        now = timezone.now()
        jobs = Job.objects.filter(is_active=True).filter(
            Q(deadline__isnull=True) | Q(deadline__gt=now)
        )
        
        query = request.GET.get('q', '')
        if query:
            jobs = jobs.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(company__name__icontains=query)
            )
        
        location = request.GET.get('location')
        if location:
            # More flexible location matching - split by comma and search for any part
            location_parts = [part.strip() for part in location.split(',')]
            location_query = Q()
            for part in location_parts:
                if part:
                    location_query |= Q(location__icontains=part)
            if location_query:
                jobs = jobs.filter(location_query)
        
        work_mode = request.GET.get('work_mode')
        if work_mode:
            jobs = jobs.filter(work_mode=work_mode)
        
        serializer = JobSerializer(jobs[:50], many=True)
        return Response(serializer.data)


class ApplyJobAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id, is_active=True)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if job is expired
        if job.deadline and job.deadline <= timezone.now():
            return Response({'error': 'This job posting has expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        if Application.objects.filter(user=request.user, job=job).exists():
            return Response({'error': 'Already applied'}, status=status.HTTP_400_BAD_REQUEST)
        
        application = Application.objects.create(
            user=request.user,
            job=job,
            cover_letter=request.data.get('cover_letter', ''),
            status='applied'
        )
        return Response({'message': 'Application submitted'}, status=status.HTTP_201_CREATED)


class SaveJobAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id, is_active=True)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
        
        SavedJob.objects.get_or_create(user=request.user, job=job)
        return Response({'message': 'Job saved'})
    
    def delete(self, request, job_id):
        try:
            job = Job.objects.get(id=job_id, is_active=True)
        except Job.DoesNotExist:
            return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)
        
        SavedJob.objects.filter(user=request.user, job=job).delete()
        return Response({'message': 'Job unsaved'})

