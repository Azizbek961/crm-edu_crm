from django.contrib import admin
from .models import Group, Subject, Teacher, Student, GroupMembership, Attendance

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'teacher', 'status']
    list_filter = ['status', 'subject']
    search_fields = ['name']

admin.site.register(Subject)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(GroupMembership)
admin.site.register(Attendance)