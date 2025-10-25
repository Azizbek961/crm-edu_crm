from django.urls import path
from . import views

urlpatterns = [
    path('groups/', views.groups_list, name='groups_list'),
    path('groups/add/', views.add_group, name='add_group'),
    path('groups/<int:group_id>/edit/', views.edit_group, name='edit_group'),
    path('groups/<int:group_id>/delete/', views.delete_group, name='delete_group'),
    path('groups/<int:group_id>/', views.group_detail, name='group_detail'),

    path('attendance/', views.attendance_list, name='attendance_list'),
    path('add/', views.attendance_add, name='attendance_add'),
    path('edit/<int:pk>/', views.attendance_edit, name='attendance_edit'),
    path('delete/<int:pk>/', views.attendance_delete, name='attendance_delete'),
    path('export/', views.attendance_export, name='attendance_export'),


    #teacher attendance
    path('teacher/attendance/', views.attendance_view, name='attendance'),
    path('teacher/attendance/save/', views.save_attendance, name='save_attendance'),
    path('teacher/attendance/get-students/', views.get_students_by_group, name='get_students_by_group'),


    # teacher_group
    path('teacher-groups/', views.teacher_groups, name='teacher_groups'),
    path('add-group/', views.add_group, name='add_group'),
    path('group/<int:group_id>/', views.group_detail, name='group_detail'),
    path('group/<int:group_id>/attendance/', views.record_attendance, name='record_attendance'),
    path('group/<int:group_id>/add-student/', views.add_student_to_group, name='add_student_to_group'),
    path('group/<int:group_id>/remove-student/<int:student_id>/', views.remove_student_from_group,
         name='remove_student_from_group'),
    path('group/<int:group_id>/available-students/', views.available_students_search, name='available_students_search'),



    path('student/groups/', views.student_groups, name='student_groups'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
]