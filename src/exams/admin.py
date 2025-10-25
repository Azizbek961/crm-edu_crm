from django.contrib import admin
from .models import Exam, Result

class ResultInline(admin.TabularInline):
    model = Result
    extra = 1

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'group', 'date', 'max_score')
    list_filter = ('subject', 'group', 'date')
    search_fields = ('name', 'subject__name', 'group__name')
    date_hierarchy = 'date'
    inlines = [ResultInline]

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'score')
    list_filter = ('exam', 'score')
    search_fields = ('exam__name', 'student__user__username')