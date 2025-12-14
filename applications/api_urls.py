from django.urls import path
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'applications', api_views.ApplicationViewSet, basename='application')

urlpatterns = router.urls

