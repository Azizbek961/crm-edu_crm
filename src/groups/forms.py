from django import forms
from education.models import Subject


class AttendanceFilterForm(forms.Form):
    SUBJECT_CHOICES = [
        ('all', 'All Subjects'),
    ]

    TIME_FILTER_CHOICES = [
        ('all', 'All Time'),
        ('week', 'This Week'),
        ('month', 'This Month'),
        ('3months', 'Last 3 Months'),
    ]

    STATUS_CHOICES = [
        ('all', 'All Status'),
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]

    subject = forms.ChoiceField(choices=SUBJECT_CHOICES, required=False)
    time_filter = forms.ChoiceField(choices=TIME_FILTER_CHOICES, required=False)
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    search = forms.CharField(required=False)