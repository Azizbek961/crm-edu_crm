from django import forms
from .models import Homework


class HomeworkFilterForm(forms.Form):
    SUBJECT_CHOICES = [
        ('all', 'All Subjects'),
    ]

    STATUS_CHOICES = [
        ('all', 'All Status'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]

    SORT_CHOICES = [
        ('due_date', 'Sort by Due Date'),
        ('subject', 'Sort by Subject'),
        ('created_at', 'Sort by Assigned Date'),
    ]

    subject = forms.ChoiceField(choices=SUBJECT_CHOICES, required=False)
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    sort = forms.ChoiceField(choices=SORT_CHOICES, required=False)