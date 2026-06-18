from rest_framework import serializers
from .models import Game, GameParameter


class GameParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameParameter
        fields = [
            'id', 'game', 'round_number', 'market_base_demand', 'seasonal_factor',
            'economic_factor', 'competition_intensity', 'cost_inflation_rate',
            'max_room_rate', 'min_room_rate',
        ]
        read_only_fields = ['game']


class GameSerializer(serializers.ModelSerializer):
    class_room_name = serializers.CharField(source='class_room.name', read_only=True)
    teams_count = serializers.SerializerMethodField()
    submitted_count = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            'id', 'name', 'class_room', 'class_room_name', 'status', 'current_round',
            'total_rounds', 'description', 'created_at', 'started_at', 'finished_at',
            'teams_count', 'submitted_count',
        ]
        read_only_fields = ['current_round', 'started_at', 'finished_at']

    def get_teams_count(self, obj):
        return obj.class_room.teams.count()

    def get_submitted_count(self, obj):
        from decisions.models import Decision
        if obj.current_round == 0:
            return 0
        return Decision.objects.filter(
            game=obj, round_number=obj.current_round, is_submitted=True
        ).count()


class GameDetailSerializer(GameSerializer):
    parameters = GameParameterSerializer(many=True, read_only=True)

    class Meta(GameSerializer.Meta):
        fields = GameSerializer.Meta.fields + ['parameters']
