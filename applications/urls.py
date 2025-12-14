from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('my-applications/', views.my_applications, name='my_applications'),
    path('<int:application_id>/', views.application_detail, name='detail'),
    path('<int:application_id>/view/', views.view_application, name='view'),
    path('<int:application_id>/reply/', views.reply_message, name='reply_message'),
    path('<int:application_id>/withdraw/', views.withdraw_application, name='withdraw'),
]

