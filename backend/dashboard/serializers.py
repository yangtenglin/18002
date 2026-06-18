from rest_framework import serializers
from .models import RoundResult, CumulativeResult


class RoundResultSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = RoundResult
        fields = [
            'id', 'team', 'team_name', 'game', 'round_number',
            'occupancy_rate_standard', 'occupancy_rate_deluxe', 'occupancy_rate_suite',
            'revenue_room', 'revenue_food', 'revenue_total',
            'cost_operation', 'cost_marketing', 'cost_staff', 'cost_renovation', 'cost_total',
            'profit', 'customer_satisfaction', 'market_share', 'score', 'calculated_at',
        ]


class CumulativeResultSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = CumulativeResult
        fields = [
            'id', 'team', 'team_name', 'game', 'rounds_played',
            'total_revenue', 'total_cost', 'total_profit',
            'avg_satisfaction', 'avg_market_share', 'final_score', 'rank', 'updated_at',
        ]


class DashboardSerializer(serializers.Serializer):
    game = serializers.DictField()
    current_round_results = RoundResultSerializer(many=True)
    cumulative_results = CumulativeResultSerializer(many=True)
    round_history = RoundResultSerializer(many=True)
