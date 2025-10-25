from django import forms
from education.models import Homework
from exams.models import Result
from groups.models import Attendance


class HomeworkSubmissionForm(forms.Form):
    submission_file = forms.FileField(required=False)
    submission_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False
    )
    homework_id = forms.IntegerField(widget=forms.HiddenInput())


class StudentFilterForm(forms.Form):
    SUBJECT_CHOICES = [
        ('', 'All Subjects'),
    ]

    STATUS_CHOICES = [
        ('', 'All Status'),
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]

    subject = forms.ChoiceField(choices=SUBJECT_CHOICES, required=False)
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))


from django import forms
from .models import User, Teacher, Student, Parent
from education.models import Subject


class AdminUserForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]

    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text="Leave blank to keep current password"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'phone', 'address', 'role', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_active': forms.Select(choices=[(True, 'Active'), (False, 'Inactive')], attrs={'class': 'form-control'}),
        }


class AdminTeacherForm(forms.ModelForm):
    class Meta:
        model = Teacher
        fields = ['qualifications']
        widgets = {
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AdminStudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['birth_date']
        widgets = {
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class AdminParentForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False
    )

    class Meta:
        model = Parent
        fields = ['students']