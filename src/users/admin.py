from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Teacher, Student, Parent

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'address')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone', 'address')}),
    )

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('user', 'hire_date')
    list_filter = ('hire_date', 'subjects')
    filter_horizontal = ('subjects',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'enrollment_date', 'birth_date')
    list_filter = ('enrollment_date',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username')

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('user',)
    filter_horizontal = ('students',)
    search_fields = ('user__first_name', 'user__last_name', 'user__username')