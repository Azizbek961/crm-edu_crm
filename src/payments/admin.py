from django.contrib import admin
from .models import Fee

@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'due_date', 'paid_date', 'status')
    list_filter = ('status', 'due_date', 'paid_date')
    search_fields = ('student__user__username', 'student__user__first_name')
    date_hierarchy = 'due_date'
    actions = ['mark_as_paid']

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid')
        self.message_user(request, f'{updated} fees marked as paid.')
    mark_as_paid.short_description = "Mark selected fees as paid"