from django.db import models
from classes.models import ClassRoom, Team


class Game(models.Model):
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('running', '进行中'),
        ('paused', '暂停'),
        ('finished', '已结束'),
    ]

    name = models.CharField(max_length=200)
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='games')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    current_round = models.IntegerField(default=0)
    total_rounds = models.IntegerField(default=8)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'game'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} (R{self.current_round}/{self.total_rounds})'


class GameParameter(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='parameters')
    round_number = models.IntegerField(default=0)
    market_base_demand = models.FloatField(default=1000)
    seasonal_factor = models.FloatField(default=1.0)
    economic_factor = models.FloatField(default=1.0)
    competition_intensity = models.FloatField(default=0.5)
    cost_inflation_rate = models.FloatField(default=0.02)
    max_room_rate = models.FloatField(default=2000)
    min_room_rate = models.FloatField(default=100)

    class Meta:
        db_table = 'game_parameter'
        unique_together = ['game', 'round_number']

    def __str__(self):
        return f'{self.game.name} - Round {self.round_number}'
