from django.urls import path
from . import views

urlpatterns = [
    # Student URLs
    path('submit/', views.submit_project, name='submit_project'),
    path('my-projects/', views.my_projects, name='my_projects'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('project/<int:project_id>/download/', views.project_download, name='project_download'),
    
    # Teacher URLs
    path('teacher/projects/', views.teacher_projects, name='teacher_projects'),
    path('teacher/project/<int:project_id>/', views.teacher_project_detail, name='teacher_project_detail'),
    path('teacher/grade/<int:project_id>/', views.grade_project, name='grade_project'),
    path('teacher/bulk-grade/', views.bulk_grade, name='bulk_grade'),
]
