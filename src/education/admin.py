from django.contrib import admin
from .models import Subject, Homework

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    list_filter = ('name',)
    search_fields = ('name', 'code')
    prepopulated_fields = {'code': ('name',)}

@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'subject', 'assigned_by', 'assigned_to', 'due_date')
    list_filter = ('subject', 'assigned_by', 'due_date')
    search_fields = ('title', 'subject__name')
    date_hierarchy = 'due_date'