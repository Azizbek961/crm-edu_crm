from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('admin/exams/', views.admin_exam_management, name='admin_exam_management'),
    path('admin/exams/create/', views.create_exam, name='create_exam'),
    path('admin/exams/<int:exam_id>/edit/', views.edit_exam, name='edit_exam'),
    path('admin/exams/<int:exam_id>/delete/', views.delete_exam, name='delete_exam'),
    path('admin/results/', views.admin_exam_results, name='admin_exam_results'),

    # Teacher exam paths
    path('teacher/exams/', views.teacher_exam_management, name='teacher_exam_management'),
    path('teacher/exams/create/', views.teacher_create_exam, name='teacher_create_exam'),
    path('teacher/exams/edit/<int:exam_id>/', views.teacher_edit_exam, name='teacher_edit_exam'),
    path('teacher/exams/delete/<int:exam_id>/', views.teacher_delete_exam, name='teacher_delete_exam'),
    path('teacher/exams/results/<int:exam_id>/', views.teacher_exam_results, name='teacher_exam_results'),
    path('teacher/exams/<int:exam_id>/results/save/', views.teacher_save_results, name='teacher_save_results'),

    # Student exam results
    path('student/results/', views.student_exam_results, name='student_exam_results'),
]