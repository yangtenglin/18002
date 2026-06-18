from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('teacher', '教师'),
        ('student', '学生'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    student_id = models.CharField(max_length=20, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')

    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return f'{self.get_role_display()}: {self.username}'
