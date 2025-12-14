from django.urls import path
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r'jobs', api_views.JobViewSet, basename='job')

urlpatterns = router.urls

urlpatterns += [
    path('jobs/search/', api_views.JobSearchAPIView.as_view(), name='api_job_search'),
    path('jobs/<int:job_id>/apply/', api_views.ApplyJobAPIView.as_view(), name='api_apply_job'),
    path('jobs/<int:job_id>/save/', api_views.SaveJobAPIView.as_view(), name='api_save_job'),
]

