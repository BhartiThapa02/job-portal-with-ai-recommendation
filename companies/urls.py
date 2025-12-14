from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.company_profile, name='profile'),
    path('profile/update/', views.update_company_profile, name='update_profile'),
    path('jobs/', views.company_jobs, name='jobs'),
    path('jobs/create/', views.create_job, name='create_job'),
    path('jobs/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    path('jobs/<int:job_id>/delete/', views.delete_job, name='delete_job'),
    path('applicants/', views.applicants, name='applicants'),
    path('applicants/<int:application_id>/', views.application_detail, name='application_detail'),
    path('applicants/<int:application_id>/update-status/', views.update_application_status, name='update_status'),
    path('applicants/<int:application_id>/message/', views.message_candidate, name='message_candidate'),
    path('applicants/<int:application_id>/download-resume/', views.download_resume, name='download_resume'),
]

