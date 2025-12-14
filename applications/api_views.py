from rest_framework import viewsets, permissions
from .models import Application
from .serializers import ApplicationSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_job_seeker:
            return Application.objects.filter(user=self.request.user)
        elif self.request.user.is_employer:
            return Application.objects.filter(job__company__user=self.request.user)
        return Application.objects.none()

