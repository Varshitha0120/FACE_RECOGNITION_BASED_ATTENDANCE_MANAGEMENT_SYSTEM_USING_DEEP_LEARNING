from django.db import models

# Create your models here.
from django.db import models

class UserProfile(models.Model):
    name = models.CharField(max_length=100)
    loginid = models.CharField(max_length=50, unique=True)
    mobile = models.CharField(max_length=10)
    password = models.CharField(max_length=128)  # Store hashed password in production
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.loginid
    
from django.db import models
from django.utils import timezone


class Attendance(models.Model):
    student_id = models.CharField(max_length=100)
    date = models.DateField(default=timezone.localdate)
    period = models.CharField(max_length=10)
    classification = models.CharField(max_length=20, default="Present")
    timestamp = models.DateTimeField(default=timezone.localtime())

    class Meta:
        unique_together = ("student_id", "date", "period")

    def __str__(self):
        return f"{self.student_id} - {self.period} - {self.timestamp}"
