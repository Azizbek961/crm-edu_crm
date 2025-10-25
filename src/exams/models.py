from django.db import models

class Exam(models.Model):
    name = models.CharField(max_length=200)
    subject = models.ForeignKey('education.Subject', on_delete=models.CASCADE)
    group = models.ForeignKey('groups.Group', on_delete=models.CASCADE)
    date = models.DateTimeField()
    max_score = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} - {self.subject}"

class Result(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    student = models.ForeignKey('users.Student', on_delete=models.CASCADE)
    score = models.PositiveIntegerField()
    remarks = models.TextField(blank=True)

    class Meta:
        unique_together = ['exam', 'student']

    def __str__(self):
        return f"{self.student} - {self.exam}: {self.score}"

    @property
    def percentage(self):
        if self.exam.max_score > 0:
            return (self.score / self.exam.max_score) * 100
        return 0