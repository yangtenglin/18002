from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import RoundResult, CumulativeResult
from .serializers import RoundResultSerializer, CumulativeResultSerializer
from simulation.models import Game
from simulation.serializers import GameSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_view(request, game_pk):
    try:
        game = Game.objects.get(pk=game_pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=404)

    game_data = GameSerializer(game).data

    current_round_results = RoundResult.objects.filter(
        game=game, round_number=game.current_round
    ) if game.current_round > 0 else RoundResult.objects.none()

    cumulative_results = CumulativeResult.objects.filter(game=game).order_by('rank')

    round_history = RoundResult.objects.filter(game=game).order_by('round_number', '-score')

    return Response({
        'game': game_data,
        'current_round_results': RoundResultSerializer(current_round_results, many=True).data,
        'cumulative_results': CumulativeResultSerializer(cumulative_results, many=True).data,
        'round_history': RoundResultSerializer(round_history, many=True).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ranking_view(request, game_pk):
    try:
        game = Game.objects.get(pk=game_pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=404)

    cumulative_results = CumulativeResult.objects.filter(game=game).order_by('rank')
    serializer = CumulativeResultSerializer(cumulative_results, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def round_result_view(request, game_pk, round_number):
    try:
        game = Game.objects.get(pk=game_pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=404)

    results = RoundResult.objects.filter(game=game, round_number=round_number).order_by('-score')
    serializer = RoundResultSerializer(results, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def team_trend_view(request, game_pk, team_pk):
    try:
        game = Game.objects.get(pk=game_pk)
    except Game.DoesNotExist:
        return Response({'detail': '模拟不存在'}, status=404)

    results = RoundResult.objects.filter(game=game, team_id=team_pk).order_by('round_number')
    serializer = RoundResultSerializer(results, many=True)
    return Response(serializer.data)
