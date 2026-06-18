from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Decision
from .serializers import DecisionSerializer
from simulation.models import Game
from classes.models import Team


def is_teacher(user):
    return user.role == 'teacher'


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def decision_list_create_view(request, game_pk):
    try:
        game = Game.objects.get(pk=game_pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        round_number = request.query_params.get('round', game.current_round)
        decisions = Decision.objects.filter(game=game, round_number=round_number)
        if not is_teacher(request.user):
            decisions = decisions.filter(team__members=request.user)
        serializer = DecisionSerializer(decisions, many=True)
        return Response(serializer.data)

    if game.status != 'running':
        return Response({'detail': '模拟未在运行中，无法提交决策'}, status=status.HTTP_400_BAD_REQUEST)

    team_id = request.data.get('team')
    try:
        team = Team.objects.get(pk=team_id, class_room=game.class_room)
    except Team.DoesNotExist:
        return Response({'detail': '团队不存在'}, status=status.HTTP_404_NOT_FOUND)

    if not is_teacher(request.user) and not team.members.filter(pk=request.user.pk).exists():
        return Response({'detail': '您不是该团队成员'}, status=status.HTTP_403_FORBIDDEN)

    existing = Decision.objects.filter(
        team=team, game=game, round_number=game.current_round
    ).first()

    if existing and existing.is_submitted:
        return Response({'detail': '本回合已提交决策，不可修改'}, status=status.HTTP_400_BAD_REQUEST)

    data = request.data.copy()
    data['game'] = game.pk
    data['round_number'] = game.current_round
    data['is_submitted'] = True

    if existing:
        serializer = DecisionSerializer(existing, data=data, partial=False)
    else:
        serializer = DecisionSerializer(data=data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED if not existing else status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def decision_detail_view(request, game_pk, pk):
    try:
        decision = Decision.objects.get(pk=pk, game_id=game_pk)
    except Decision.DoesNotExist:
        return Response({'detail': '决策不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        if not is_teacher(request.user) and not decision.team.members.filter(pk=request.user.pk).exists():
            return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
        serializer = DecisionSerializer(decision)
        return Response(serializer.data)

    if decision.is_submitted:
        return Response({'detail': '已提交的决策不可修改'}, status=status.HTTP_400_BAD_REQUEST)

    if not is_teacher(request.user) and not decision.team.members.filter(pk=request.user.pk).exists():
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)

    serializer = DecisionSerializer(decision, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_decision_view(request, game_pk):
    try:
        game = Game.objects.get(pk=game_pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if is_teacher(request.user):
        return Response({'detail': '教师无决策'}, status=status.HTTP_400_BAD_REQUEST)

    teams = Team.objects.filter(class_room=game.class_room, members=request.user)
    if not teams.exists():
        return Response({'detail': '您不在任何团队中'}, status=status.HTTP_404_NOT_FOUND)

    team = teams.first()
    decision = Decision.objects.filter(
        team=team, game=game, round_number=game.current_round
    ).first()

    if decision:
        serializer = DecisionSerializer(decision)
        return Response(serializer.data)
    return Response({'detail': '尚未提交决策', 'team_id': team.pk}, status=status.HTTP_404_NOT_FOUND)
