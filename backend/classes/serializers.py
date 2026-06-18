from rest_framework import serializers
from .models import ClassRoom, Team
from users.serializers import UserBriefSerializer


class TeamSerializer(serializers.ModelSerializer):
    members_detail = UserBriefSerializer(source='members', many=True, read_only=True)
    captain_detail = UserBriefSerializer(source='captain', read_only=True)

    class Meta:
        model = Team
        fields = ['id', 'name', 'class_room', 'members', 'captain', 'members_detail', 'captain_detail', 'created_at']
        extra_kwargs = {
            'members': {'write_only': True},
            'captain': {'write_only': True},
        }


class ClassRoomSerializer(serializers.ModelSerializer):
    teams_count = serializers.SerializerMethodField()
    students_count = serializers.SerializerMethodField()

    class Meta:
        model = ClassRoom
        fields = ['id', 'name', 'code', 'teacher', 'description', 'created_at', 'is_active', 'teams_count', 'students_count']
        read_only_fields = ['teacher', 'code']

    def get_teams_count(self, obj):
        return obj.teams.count()

    def get_students_count(self, obj):
        from users.models import User
        team_ids = obj.teams.values_list('id', flat=True)
        return User.objects.filter(teams__id__in=team_ids).distinct().count()


class ClassRoomDetailSerializer(ClassRoomSerializer):
    teams = TeamSerializer(many=True, read_only=True)

    class Meta(ClassRoomSerializer.Meta):
        fields = ClassRoomSerializer.Meta.fields + ['teams']
