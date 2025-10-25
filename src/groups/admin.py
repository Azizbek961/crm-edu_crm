from django.contrib import admin
from .models import Group, GroupMembership, Attendance

class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'teacher')
    list_filter = ('subject', 'teacher')
    search_fields = ('name', 'subject__name', 'teacher__user__username')
    inlines = [GroupMembershipInline]

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'joined_date')
    list_filter = ('joined_date', 'group')
    search_fields = ('student__user__username', 'group__name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'date', 'status', 'recorded_by')
    list_filter = ('date', 'status', 'group')
    search_fields = ('student__user__username', 'group__name')
    date_hierarchy = 'date'