from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout

from .models import User
from .serializers import UserSerializer, RegisterSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'user': UserSerializer(user).data,
            'message': '注册成功',
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    role = request.data.get('role')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        if role and user.role != role:
            role_display = dict(User.ROLE_CHOICES).get(role, role)
            return Response(
                {'detail': f'该账号不是{role_display}身份，请选择正确的登录入口'},
                status=status.HTTP_403_FORBIDDEN,
            )
        login(request, user)
        return Response({
            'user': UserSerializer(user).data,
            'message': '登录成功',
        })
    return Response({'detail': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'message': '已退出登录'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_view(request):
    return Response(UserSerializer(request.user).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list_view(request):
    role = request.query_params.get('role')
    users = User.objects.all()
    if role:
        users = users.filter(role=role)
    serializer = UserSerializer(users, many=True)
    return Response(serializer.data)
