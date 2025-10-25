from django.db import models

class Fee(models.Model):
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=(
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('overdue', 'Overdue'),
    ), default='pending')

    def __str__(self):
        return f"{self.student} - {self.amount} ({self.status})"