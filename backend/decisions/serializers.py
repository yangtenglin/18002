from rest_framework import serializers
from .models import Decision


class DecisionSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = Decision
        fields = [
            'id', 'team', 'team_name', 'game', 'round_number',
            'room_rate_standard', 'room_rate_deluxe', 'room_rate_suite',
            'food_budget', 'marketing_budget', 'staff_training_budget',
            'renovation_budget', 'service_quality_target',
            'submitted_at', 'is_submitted',
        ]
        read_only_fields = ['submitted_at', 'is_submitted']
