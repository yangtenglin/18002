import uuid
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import User
from .models import ClassRoom, Team
from .serializers import ClassRoomSerializer, ClassRoomDetailSerializer, TeamSerializer


def is_teacher(user):
    return user.role == 'teacher'


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def classroom_list_create_view(request):
    if request.method == 'GET':
        if is_teacher(request.user):
            classrooms = ClassRoom.objects.filter(teacher=request.user)
        else:
            classrooms = ClassRoom.objects.filter(
                teams__members=request.user
            ).distinct()
        serializer = ClassRoomSerializer(classrooms, many=True)
        return Response(serializer.data)

    if not is_teacher(request.user):
        return Response({'detail': '只有教师可以创建班级'}, status=status.HTTP_403_FORBIDDEN)

    serializer = ClassRoomSerializer(data=request.data)
    if serializer.is_valid():
        classroom = serializer.save(teacher=request.user, code=uuid.uuid4().hex[:8].upper())
        return Response(ClassRoomSerializer(classroom).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def classroom_detail_view(request, pk):
    try:
        classroom = ClassRoom.objects.get(pk=pk)
    except ClassRoom.DoesNotExist:
        return Response({'detail': '班级不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = ClassRoomDetailSerializer(classroom)
        return Response(serializer.data)

    if not is_teacher(request.user) or classroom.teacher != request.user:
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = ClassRoomSerializer(classroom, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        classroom.delete()
        return Response({'message': '已删除'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def team_list_create_view(request, classroom_pk):
    try:
        classroom = ClassRoom.objects.get(pk=classroom_pk)
    except ClassRoom.DoesNotExist:
        return Response({'detail': '班级不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        teams = classroom.teams.all()
        serializer = TeamSerializer(teams, many=True)
        return Response(serializer.data)

    if not is_teacher(request.user) or classroom.teacher != request.user:
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)

    serializer = TeamSerializer(data=request.data)
    if serializer.is_valid():
        team = serializer.save(class_room=classroom)
        return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def team_detail_view(request, classroom_pk, pk):
    try:
        team = Team.objects.get(pk=pk, class_room_id=classroom_pk)
    except Team.DoesNotExist:
        return Response({'detail': '团队不存在'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = TeamSerializer(team)
        return Response(serializer.data)

    if not is_teacher(request.user) or team.class_room.teacher != request.user:
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = TeamSerializer(team, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        team.delete()
        return Response({'message': '已删除'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def team_add_member_view(request, classroom_pk, pk):
    if not is_teacher(request.user):
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    try:
        team = Team.objects.get(pk=pk, class_room_id=classroom_pk)
    except Team.DoesNotExist:
        return Response({'detail': '团队不存在'}, status=status.HTTP_404_NOT_FOUND)

    user_ids = request.data.get('user_ids', [])
    users = User.objects.filter(id__in=user_ids, role='student')
    team.members.add(*users)
    return Response(TeamSerializer(team).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def team_remove_member_view(request, classroom_pk, pk):
    if not is_teacher(request.user):
        return Response({'detail': '无权限'}, status=status.HTTP_403_FORBIDDEN)
    try:
        team = Team.objects.get(pk=pk, class_room_id=classroom_pk)
    except Team.DoesNotExist:
        return Response({'detail': '团队不存在'}, status=status.HTTP_404_NOT_FOUND)

    user_ids = request.data.get('user_ids', [])
    team.members.remove(*user_ids)
    return Response(TeamSerializer(team).data)
