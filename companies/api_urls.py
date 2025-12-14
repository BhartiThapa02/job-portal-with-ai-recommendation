from django.urls import path
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'companies', api_views.CompanyViewSet, basename='company')

urlpatterns = router.urls

