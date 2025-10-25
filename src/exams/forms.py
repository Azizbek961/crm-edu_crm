from django import forms
from education.models import Subject
from groups.models import Group
from users.models import Student
from .models import Exam, Result

class ExamResultFilterForm(forms.Form):
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        empty_label="All Subjects",
        widget=forms.Select(attrs={
            'class': 'btn btn-secondary',
            'placeholder': 'Select a subject...'
        })
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        empty_label="All Groups",
        widget=forms.Select(attrs={
            'class': 'btn btn-secondary',
            'placeholder': 'Choose a group...'
        })
    )
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.all(),
        required=False,
        empty_label="All Exams",
        widget=forms.Select(attrs={
            'class': 'btn btn-secondary',
            'placeholder': 'Pick an exam...'
        })
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        empty_label="All Students",
        widget=forms.Select(attrs={
            'class': 'btn btn-secondary',
            'placeholder': 'Search a student...'
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'btn btn-secondary',
            'placeholder': 'Start date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'btn btn-secondary',
            'placeholder': 'End date'
        })
    )


from django import forms
from education.models import Subject
from groups.models import Group
from users.models import Student
from .models import Exam, Result
from django.utils import timezone


class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['name', 'subject', 'group', 'date', 'max_score']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter exam name'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-control'
            }),
            'group': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter max score'
            }),
        }

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now():
            raise forms.ValidationError("Exam date cannot be in the past.")
        return date


class ExamResultFilterForm(forms.Form):
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        empty_label="All Subjects",
        widget=forms.Select(attrs={
            'class': 'select-control',
        })
    )
    group = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        empty_label="All Groups",
        widget=forms.Select(attrs={
            'class': 'select-control',
        })
    )
    exam = forms.ModelChoiceField(
        queryset=Exam.objects.all(),
        required=False,
        empty_label="All Exams",
        widget=forms.Select(attrs={
            'class': 'select-control',
        })
    )
    student = forms.ModelChoiceField(
        queryset=Student.objects.all(),
        required=False,
        empty_label="All Students",
        widget=forms.Select(attrs={
            'class': 'select-control',
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'input-control',
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'input-control',
        })
    )

from django import forms
from education.models import Subject
from groups.models import Group
from users.models import Student
from .models import Exam, Result
from django.utils import timezone


class StudentExamFilterForm(forms.Form):
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        required=False,
        empty_label="All Subjects",
        widget=forms.Select(attrs={
            'class': 'filter-btn',
        })
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'filter-btn',
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'filter-btn',
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'All Status'), ('passed', 'Passed'), ('failed', 'Failed')],
        required=False,
        widget=forms.Select(attrs={
            'class': 'filter-btn',
        })
    )


# exams/forms.py (add these forms)
from django import forms
from education.models import Subject
from groups.models import Group
from users.models import Student, Teacher
from .models import Exam, Result
from django.utils import timezone


class TeacherExamForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if self.teacher:
            # Only show groups that this teacher teaches
            self.fields['group'].queryset = Group.objects.filter(teacher=self.teacher)
            # Only show subjects that this teacher teaches
            self.fields['subject'].queryset = self.teacher.subjects.all()

    class Meta:
        model = Exam
        fields = ['name', 'subject', 'group', 'date', 'max_score']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter exam name'
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select'
            }),
            'group': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-input'
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter max score',
                'min': 1,
                'max': 1000
            }),
        }

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now():
            raise forms.ValidationError("Exam date cannot be in the past.")
        return date


class TeacherResultForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = ['score', 'remarks']
        widgets = {
            'score': forms.NumberInput(attrs={
                'class': 'score-input',
                'min': 0
            }),
            'remarks': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter remark'
            })
        }