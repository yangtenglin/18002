from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Game, GameParameter
from .serializers import GameSerializer, GameDetailSerializer, GameParameterSerializer
from .engine import SimulationEngine


def is_teacher(user):
    return user.role == 'teacher'


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def game_list_create_view(request):
    if request.method == 'GET':
        class_room_id = request.query_params.get('class_room')
        games = Game.objects.all()
        if class_room_id:
            games = games.filter(class_room_id=class_room_id)
        if not is_teacher(request.user):
            games = games.filter(class_room__teams__members=request.user).distinct()
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)

    if not is_teacher(request.user):
        return Response({'detail': '只有教师可以创建模拟'}, status=status.HTTP_403_FORBIDDEN)

    serializer = GameSerializer(data=request.data)
    if serializer.is_valid():
        game = serializer.save()
        GameParameter.objects.create(game=game, round_number=0)
        for rn in range(1, game.total_rounds + 1):
            GameParameter.objects.create(
                game=game,
                round_number=rn,
                market_base_demand=1000 + rn * 50,
                seasonal_factor=round(1.0 + 0.1 * ((rn % 4) - 1.5), 2),
                economic_factor=1.0,
                competition_intensity=0.5,
            )
        return Response(GameDetailSerializer(game).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def game_detail_view(request, pk):
    try:
        game = Game.objects.get(pk=pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = GameDetailSerializer(game)
        return Response(serializer.data)

    if not is_teacher(request.user) or game.class_room.teacher != request.user:
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = GameSerializer(game, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        game.delete()
        return Response({'message': '已删除'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def game_start_view(request, pk):
    if not is_teacher(request.user):
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    try:
        game = Game.objects.get(pk=pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if game.status not in ('draft', 'paused'):
        return Response({'detail': f'当前状态 {game.get_status_display()} 不可启动'}, status=status.HTTP_400_BAD_REQUEST)

    game.status = 'running'
    game.current_round += 1
    if not game.started_at:
        game.started_at = timezone.now()
    game.save()
    return Response(GameDetailSerializer(game).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def game_pause_view(request, pk):
    if not is_teacher(request.user):
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    try:
        game = Game.objects.get(pk=pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if game.status != 'running':
        return Response({'detail': '当前状态不可暂停'}, status=status.HTTP_400_BAD_REQUEST)

    game.status = 'paused'
    game.save()
    return Response(GameDetailSerializer(game).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def game_advance_round_view(request, pk):
    if not is_teacher(request.user):
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    try:
        game = Game.objects.get(pk=pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if game.status != 'running':
        return Response({'detail': '模拟未在运行中'}, status=status.HTTP_400_BAD_REQUEST)

    from decisions.models import Decision
    submitted = Decision.objects.filter(
        game=game, round_number=game.current_round, is_submitted=True
    ).count()
    total_teams = game.class_room.teams.count()

    engine = SimulationEngine()
    engine.calculate_round(game, game.current_round)

    if game.current_round >= game.total_rounds:
        game.status = 'finished'
        game.finished_at = timezone.now()
        game.save()
    else:
        game.current_round += 1
        game.save()

    return Response(GameDetailSerializer(game).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def game_parameter_list_view(request, game_pk):
    try:
        game = Game.objects.get(pk=game_pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        params = game.parameters.all()
        serializer = GameParameterSerializer(params, many=True)
        return Response(serializer.data)

    if not is_teacher(request.user) or game.class_room.teacher != request.user:
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)

    serializer = GameParameterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(game=game)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def game_parameter_update_view(request, game_pk, pk):
    if not is_teacher(request.user):
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    try:
        param = GameParameter.objects.get(pk=pk, game_id=game_pk)
    except GameParameter.DoesNotExist:
        return Response({'detail': '参数不存在'}, status=status.HTTP_404_NOT_FOUND)

    serializer = GameParameterSerializer(param, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
