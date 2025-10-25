# education/urls.py
from django.urls import path
from . import views

app_name = 'education'

urlpatterns = [
    # Subject URLs (Admin only)
    path('', views.courses_dashboard, name='courses_dashboard'),
    path('add/', views.add_subject, name='add_subject'),
    path('<int:pk>/edit/', views.edit_subject, name='edit_subject'),
    path('<int:pk>/view/', views.view_subject, name='view_subject'),
    path('<int:pk>/delete/', views.delete_subject, name='delete_subject'),

    # Student Homework URLs
    path('homework/', views.student_homework, name='student_homework'),
    path('homework/<int:pk>/mark-done/', views.mark_homework_done, name='mark_homework_done'),

    # Teacher Homework URLs (Teacher only - manage their own homework)
    path('teacher/homework/', views.teacher_homework, name='teacher_homework'),
    path('teacher/homework/add/', views.teacher_add_homework, name='teacher_add_homework'),
    path('teacher/homework/<int:pk>/edit/', views.teacher_edit_homework, name='teacher_edit_homework'),
    path('teacher/homework/<int:pk>/delete/', views.teacher_delete_homework, name='teacher_delete_homework'),

    # Admin Homework URLs (Admin only - manage all homework)
    path('admin/homework/', views.admin_homework, name='admin_homework'),
    path('admin/homework/add/', views.admin_add_homework, name='admin_add_homework'),
    path('admin/homework/<int:pk>/edit/', views.admin_edit_homework, name='admin_edit_homework'),
    path('admin/homework/<int:pk>/delete/', views.admin_delete_homework, name='admin_delete_homework'),
]