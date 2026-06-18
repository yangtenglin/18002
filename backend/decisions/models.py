from django.db import models
from django.core.validators import MinValueValidator
from classes.models import Team
from simulation.models import Game


class Decision(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='decisions')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='decisions')
    round_number = models.IntegerField()
    room_rate_standard = models.FloatField(validators=[MinValueValidator(0)], default=500)
    room_rate_deluxe = models.FloatField(validators=[MinValueValidator(0)], default=800)
    room_rate_suite = models.FloatField(validators=[MinValueValidator(0)], default=1500)
    food_budget = models.FloatField(validators=[MinValueValidator(0)], default=50000)
    marketing_budget = models.FloatField(validators=[MinValueValidator(0)], default=30000)
    staff_training_budget = models.FloatField(validators=[MinValueValidator(0)], default=20000)
    renovation_budget = models.FloatField(validators=[MinValueValidator(0)], default=10000)
    service_quality_target = models.FloatField(validators=[MinValueValidator(0)], default=7.0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_submitted = models.BooleanField(default=False)

    class Meta:
        db_table = 'decision'
        unique_together = ['team', 'game', 'round_number']
        ordering = ['-round_number']

    def __str__(self):
        return f'{self.team.name} - {self.game.name} - R{self.round_number}'
