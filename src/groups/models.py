from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
class Group(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('completed', 'Completed'),
        ('hold', 'On Hold'),
    )
    name = models.CharField(max_length=100)
    subject = models.ForeignKey('education.Subject', on_delete=models.CASCADE)
    teacher = models.ForeignKey('users.Teacher', on_delete=models.CASCADE)
    students = models.ManyToManyField('users.Student', through='GroupMembership')
    schedule = models.JSONField()  # Stores class schedule data
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.name} - {self.subject}"

class GroupMembership(models.Model):
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    joined_date = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'group']

    def __str__(self):
        return f"{self.student} in {self.group}"

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    )
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=7, choices=STATUS_CHOICES)
    recorded_by = models.ForeignKey('users.User', on_delete=models.CASCADE)
    # recorded_by_admin = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.CASCADE,
    #     related_name="attendances_recorded"
    # )
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'group', 'date']
        ordering = ['-date', 'student']

    def clean(self):
        # Check if student belongs to the group
        if not GroupMembership.objects.filter(student=self.student, group=self.group).exists():
            raise ValidationError(f"Student {self.student} is not a member of {self.group}")

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"



