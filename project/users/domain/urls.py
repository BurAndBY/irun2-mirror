from django.urls import path

from . import views

urlpatterns = [
    path('student-info/', views.StudentInfoView.as_view(), name='domain_student_info'),
]
