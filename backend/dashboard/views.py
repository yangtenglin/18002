from django.db.models import Prefetch
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import RoundResult, CumulativeResult
from .serializers import RoundResultSerializer, CumulativeResultSerializer
from simulation.models import Game
from simulation.serializers import GameSerializer, GameDetailSerializer
from backend.cache import cache_api_view, BatchSubmittedCounter


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_api_view(timeout=2, key_prefix='dashboard')
def dashboard_view(request, game_pk):
    try:
        game = Game.objects.select_related('class_room').prefetch_related(
            Prefetch(
                'round_results',
                queryset=RoundResult.objects.select_related('team').order_by('round_number', '-score'),
                to_attr='_round_history',
            ),
            Prefetch(
                'cumulative_results',
                queryset=CumulativeResult.objects.select_related('team').order_by('rank'),
                to_attr='_cumulative',
            ),
            Prefetch(
                'parameters',
                queryset=None,
                to_attr='_params',
            ),
        ).get(pk=game_pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=404)

    submitted_map = BatchSubmittedCounter.build_map([game])
    ctx = {'submitted_map': submitted_map}

    current_round_results = [
        r for r in getattr(game, '_round_history', [])
        if r.round_number == game.current_round
    ]

    round_history = getattr(game, '_round_history', [])
    cumulative = getattr(game, '_cumulative', [])

    return Response({
        'game': GameSerializer(game, context=ctx).data,
        'current_round_results': RoundResultSerializer(current_round_results, many=True).data,
        'cumulative_results': CumulativeResultSerializer(cumulative, many=True).data,
        'round_history': RoundResultSerializer(round_history, many=True).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_api_view(timeout=3, key_prefix='ranking')
def ranking_view(request, game_pk):
    cumulative_results = CumulativeResultSerializer.optimize_queryset(
        CumulativeResult.objects.filter(game_id=game_pk).order_by('rank')
    )
    if not cumulative_results.exists():
        try:
            Game.objects.get(pk=game_pk)
        except Game.DoesNotExist:
            return Response({'detail': '模拟不存在'}, status=404)
    serializer = CumulativeResultSerializer(cumulative_results, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_api_view(timeout=5, key_prefix='round_result')
def round_result_view(request, game_pk, round_number):
    results = RoundResultSerializer.optimize_queryset(
        RoundResult.objects.filter(
            game_id=game_pk, round_number=round_number
        ).order_by('-score')
    )
    if not results.exists():
        try:
            Game.objects.get(pk=game_pk)
        except Game.DoesNotExist:
            return Response({'detail': '模拟不存在'}, status=404)
    serializer = RoundResultSerializer(results, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@cache_api_view(timeout=3, key_prefix='team_trend')
def team_trend_view(request, game_pk, team_pk):
    results = RoundResultSerializer.optimize_queryset(
        RoundResult.objects.filter(
            game_id=game_pk, team_id=team_pk
        ).order_by('round_number')
    )
    if not results.exists():
        try:
            Game.objects.get(pk=game_pk)
        except Game.DoesNotExist:
            return Response({'detail': '模拟不存在'}, status=404)
    serializer = RoundResultSerializer(results, many=True)
    return Response(serializer.data)
