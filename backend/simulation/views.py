from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Game, GameParameter
from .serializers import GameSerializer, GameDetailSerializer, GameParameterSerializer
from .engine import SimulationEngine
from backend.cache import cache_api_view, BatchSubmittedCounter, cache


def is_teacher(user):
    return user.role == 'teacher'


def _invalidate_game_cache(game_pk):
    keys = [
        f'api:*{game_pk}*',
        f'dashboard:*{game_pk}*',
        f'ranking:*{game_pk}*',
        f'round_result:*{game_pk}*',
        f'team_trend:*{game_pk}*',
        f'decision:*{game_pk}*',
        f'my_decision:*{game_pk}*',
    ]
    try:
        cache.delete_many(keys)
    except Exception:
        pass


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@cache_api_view(timeout=2, key_prefix='api')
def game_list_create_view(request):
    if request.method == 'GET':
        class_room_id = request.query_params.get('class_room')
        games = Game.objects.all()
        if class_room_id:
            games = games.filter(class_room_id=class_room_id)
        if not is_teacher(request.user):
            games = games.filter(class_room__teams__members=request.user).distinct()

        games = GameSerializer.optimize_queryset(games)
        games_list = list(games)
        submitted_map = BatchSubmittedCounter.build_map(games_list)

        serializer = GameSerializer(
            games_list, many=True, context={'submitted_map': submitted_map}
        )
        return Response(serializer.data)

    if not is_teacher(request.user):
        return Response({'detail': '只有教师可以创建模拟'}, status=status.HTTP_403_FORBIDDEN)

    serializer = GameSerializer(data=request.data)
    if serializer.is_valid():
        with transaction.atomic():
            game = serializer.save()
            params = [GameParameter(game=game, round_number=0)]
            for rn in range(1, game.total_rounds + 1):
                params.append(GameParameter(
                    game=game,
                    round_number=rn,
                    market_base_demand=1000 + rn * 50,
                    seasonal_factor=round(1.0 + 0.1 * ((rn % 4) - 1.5), 2),
                    economic_factor=1.0,
                    competition_intensity=0.5,
                ))
            GameParameter.objects.bulk_create(params)

        return Response(GameDetailSerializer(game).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
@cache_api_view(timeout=2, key_prefix='api')
def game_detail_view(request, pk):
    if request.method == 'GET':
        try:
            game = GameDetailSerializer.optimize_queryset(
                Game.objects.filter(pk=pk)
            ).get()
        except Game.DoesNotExist:
            return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

        submitted_map = BatchSubmittedCounter.build_map([game])
        serializer = GameDetailSerializer(
            game, context={'submitted_map': submitted_map}
        )
        return Response(serializer.data)

    try:
        game = Game.objects.select_related('class_room').get(pk=pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if not is_teacher(request.user) or game.class_room.teacher != request.user:
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = GameSerializer(game, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            _invalidate_game_cache(pk)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        game.delete()
        _invalidate_game_cache(pk)
        return Response({'message': '已删除'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def game_start_view(request, pk):
    if not is_teacher(request.user):
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    try:
        game = Game.objects.select_related('class_room').get(pk=pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if game.status not in ('draft', 'paused'):
        return Response({'detail': f'当前状态 {game.get_status_display()} 不可启动'}, status=status.HTTP_400_BAD_REQUEST)

    game.status = 'running'
    game.current_round += 1
    if not game.started_at:
        game.started_at = timezone.now()
    game.save()
    _invalidate_game_cache(pk)
    return Response(GameDetailSerializer(game).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def game_pause_view(request, pk):
    if not is_teacher(request.user):
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    try:
        game = Game.objects.select_related('class_room').get(pk=pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if game.status != 'running':
        return Response({'detail': '当前状态不可暂停'}, status=status.HTTP_400_BAD_REQUEST)

    game.status = 'paused'
    game.save()
    _invalidate_game_cache(pk)
    return Response(GameDetailSerializer(game).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def game_advance_round_view(request, pk):
    if not is_teacher(request.user):
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    try:
        game = Game.objects.select_related('class_room').prefetch_related(
            'class_room__teams'
        ).get(pk=pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if game.status != 'running':
        return Response({'detail': '模拟未在运行中'}, status=status.HTTP_400_BAD_REQUEST)

    from decisions.models import Decision
    submitted = Decision.objects.filter(
        game_id=pk, round_number=game.current_round, is_submitted=True
    ).count()
    total_teams = game.class_room.teams.count()

    engine = SimulationEngine()
    with transaction.atomic():
        engine.calculate_round(game, game.current_round)

        if game.current_round >= game.total_rounds:
            game.status = 'finished'
            game.finished_at = timezone.now()
            game.save(update_fields=['status', 'finished_at'])
        else:
            game.current_round += 1
            game.save(update_fields=['current_round'])

    _invalidate_game_cache(pk)
    return Response(GameDetailSerializer(game).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@cache_api_view(timeout=5, key_prefix='api')
def game_parameter_list_view(request, game_pk):
    try:
        game = Game.objects.select_related('class_room').prefetch_related(
            'parameters'
        ).get(pk=game_pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        params = list(game.parameters.all())
        serializer = GameParameterSerializer(params, many=True)
        return Response(serializer.data)

    if not is_teacher(request.user) or game.class_room.teacher != request.user:
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)

    serializer = GameParameterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(game=game)
        _invalidate_game_cache(game_pk)
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
        _invalidate_game_cache(game_pk)
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
