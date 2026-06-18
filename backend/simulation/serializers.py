from django.db.models import Count
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
    teams_count = serializers.IntegerField(read_only=True, default=0)
    submitted_count = serializers.SerializerMethodField()

    class Meta:
        model = Game
        fields = [
            'id', 'name', 'class_room', 'class_room_name', 'status', 'current_round',
            'total_rounds', 'description', 'created_at', 'started_at', 'finished_at',
            'teams_count', 'submitted_count',
        ]
        read_only_fields = ['current_round', 'started_at', 'finished_at']

    def get_submitted_count(self, obj):
        if obj.current_round == 0:
            return 0
        submitted_map = self.context.get('submitted_map', {})
        if submitted_map:
            return submitted_map.get(obj.pk, 0)
        from decisions.models import Decision
        return Decision.objects.filter(
            game=obj, round_number=obj.current_round, is_submitted=True
        ).count()

    @staticmethod
    def optimize_queryset(queryset):
        return queryset.select_related('class_room').annotate(
            _teams_count=Count('class_room__teams', distinct=True)
        )

    def to_representation(self, instance):
        if hasattr(instance, '_teams_count'):
            instance.teams_count = instance._teams_count
        return super().to_representation(instance)


class GameDetailSerializer(GameSerializer):
    parameters = GameParameterSerializer(many=True, read_only=True)

    class Meta(GameSerializer.Meta):
        fields = GameSerializer.Meta.fields + ['parameters']

    @staticmethod
    def optimize_queryset(queryset):
        return GameSerializer.optimize_queryset(
            queryset.prefetch_related('parameters')
        )
