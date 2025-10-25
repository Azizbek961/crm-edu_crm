from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.contrib.auth.decorators import login_required
from .decorators import admin_required, teacher_required, student_required


urlpatterns = [
    # admin dashboard
    path('', views.CustomLoginView.as_view(), name='login'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Teacher dashboard and features
    path('teacher/dashboard/', login_required(teacher_required(views.teacher_dashboard)), name='teacher_dashboard'),
    path('teacher/classes/', login_required(teacher_required(views.teacher_classes)), name='teacher_classes'),
    path('teacher/students/', login_required(teacher_required(views.teacher_students)), name='teacher_students'),
    path('teacher/homework/', login_required(teacher_required(views.teacher_homework)), name='teacher_homework'),
    path('teacher/exams/', login_required(teacher_required(views.teacher_exams)), name='teacher_exams'),
    path('teacher/attendance/', login_required(teacher_required(views.teacher_attendance)), name='teacher_attendance'),

    # Student dashboard
    path('student/dashboard/', login_required(student_required(views.student_dashboard)), name='student_dashboard'),

    # admin-students
    path('students/', login_required(views.StudentListView.as_view()), name='student_list'),
    path('students/add/', login_required(views.StudentCreateView.as_view()), name='student_add'),
    path('students/<int:pk>/edit/', login_required(views.StudentUpdateView.as_view()), name='student_edit'),
    path('students/<int:pk>/delete/', login_required(views.StudentDeleteView.as_view()), name='student_delete'),
    path('students/<int:pk>/', login_required(views.StudentDetailView.as_view()), name='student_detail'),

    # API endpoints for dynamic data
    path('api/students/stats/', login_required(views.student_stats_api), name='student_stats_api'),
    path('api/students/data/', login_required(views.student_data_api), name='student_data_api'),

    # admin-teachers
    path('list/', views.teachers_list, name='teachers_list'),
    path('add/', views.add_teacher, name='add_teacher'),
    path('edit/<int:teacher_id>/', views.edit_teacher, name='edit_teacher'),
    path('delete/<int:teacher_id>/', views.delete_teacher, name='delete_teacher'),

    # Admin Users Management
    path('users/admin/users/', login_required(admin_required(views.admin_users_management)), name='admin_users_management'),
    path('users/admin/users/add/', login_required(admin_required(views.admin_add_user)), name='admin_add_user'),
    path('users/admin/users/<int:user_id>/edit/', login_required(admin_required(views.admin_edit_user)), name='admin_edit_user'),
    path('users/admin/users/<int:user_id>/delete/', login_required(admin_required(views.admin_delete_user)), name='admin_delete_user'),
]
