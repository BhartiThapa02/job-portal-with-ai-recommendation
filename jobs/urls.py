from django.urls import path
from . import views

app_name = 'jobs'

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_jobs, name='search'),
    path('<int:job_id>/', views.job_detail, name='detail'),
    path('<int:job_id>/apply/', views.apply_job, name='apply'),
    path('<int:job_id>/save/', views.save_job, name='save'),
    path('saved/', views.saved_jobs, name='saved'),
    path('recommendations/', views.recommendations, name='recommendations'),
]

