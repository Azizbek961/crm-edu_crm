from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        permissions = [
            ("view_statistics", "Can view statistics"),
            ("manage_groups", "Can manage groups"),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    subjects = models.ManyToManyField('education.Subject', blank=True)
    hire_date = models.DateField(auto_now_add=True)
    qualifications = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    enrollment_date = models.DateField(auto_now_add=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    students = models.ManyToManyField(Student, related_name='parents')

    def __str__(self):
        return self.user.get_full_name() or self.user.username