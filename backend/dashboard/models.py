from django.db import models
from classes.models import Team
from simulation.models import Game


class RoundResult(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='round_results')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='round_results')
    round_number = models.IntegerField()
    occupancy_rate_standard = models.FloatField(default=0)
    occupancy_rate_deluxe = models.FloatField(default=0)
    occupancy_rate_suite = models.FloatField(default=0)
    revenue_room = models.FloatField(default=0)
    revenue_food = models.FloatField(default=0)
    revenue_total = models.FloatField(default=0)
    cost_operation = models.FloatField(default=0)
    cost_marketing = models.FloatField(default=0)
    cost_staff = models.FloatField(default=0)
    cost_renovation = models.FloatField(default=0)
    cost_total = models.FloatField(default=0)
    profit = models.FloatField(default=0)
    customer_satisfaction = models.FloatField(default=0)
    market_share = models.FloatField(default=0)
    score = models.FloatField(default=0)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'round_result'
        unique_together = ['team', 'game', 'round_number']
        ordering = ['round_number']

    def __str__(self):
        return f'{self.team.name} - R{self.round_number} - Score:{self.score}'


class CumulativeResult(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='cumulative_results')
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='cumulative_results')
    rounds_played = models.IntegerField(default=0)
    total_revenue = models.FloatField(default=0)
    total_cost = models.FloatField(default=0)
    total_profit = models.FloatField(default=0)
    avg_satisfaction = models.FloatField(default=0)
    avg_market_share = models.FloatField(default=0)
    final_score = models.FloatField(default=0)
    rank = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cumulative_result'
        unique_together = ['team', 'game']
        ordering = ['-final_score']

    def __str__(self):
        return f'{self.team.name} - Rank:{self.rank} - Score:{self.final_score}'
