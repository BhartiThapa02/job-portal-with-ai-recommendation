from rest_framework import viewsets, permissions
from .models import Company
from .serializers import CompanySerializer


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_employer:
            return Company.objects.filter(user=self.request.user)
        return Company.objects.filter(is_verified=True)

