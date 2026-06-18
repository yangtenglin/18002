from django.db import models
from users.models import User


class ClassRoom(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_classes')
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'class_room'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=100)
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='teams')
    members = models.ManyToManyField(User, related_name='teams', blank=True)
    captain = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='led_teams')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'team'
        unique_together = ['name', 'class_room']
        ordering = ['name']

    def __str__(self):
        return f'{self.class_room.name} - {self.name}'
