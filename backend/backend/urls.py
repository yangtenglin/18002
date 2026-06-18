from django.contrib import admin
from django.urls import path, include
from users.views import register_view, login_view, logout_view, current_user_view, user_list_view
from classes.views import (
    classroom_list_create_view, classroom_detail_view,
    team_list_create_view, team_detail_view,
    team_add_member_view, team_remove_member_view,
)
from simulation.views import (
    game_list_create_view, game_detail_view,
    game_start_view, game_pause_view, game_advance_round_view,
    game_parameter_list_view, game_parameter_update_view,
)
from decisions.views import (
    decision_list_create_view, decision_detail_view, my_decision_view,
)
from dashboard.views import dashboard_view, ranking_view, round_result_view, team_trend_view

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/register/', register_view, name='register'),
    path('api/auth/login/', login_view, name='login'),
    path('api/auth/logout/', logout_view, name='logout'),
    path('api/auth/me/', current_user_view, name='current-user'),
    path('api/users/', user_list_view, name='user-list'),

    path('api/classrooms/', classroom_list_create_view, name='classroom-list'),
    path('api/classrooms/<int:pk>/', classroom_detail_view, name='classroom-detail'),
    path('api/classrooms/<int:classroom_pk>/teams/', team_list_create_view, name='team-list'),
    path('api/classrooms/<int:classroom_pk>/teams/<int:pk>/', team_detail_view, name='team-detail'),
    path('api/classrooms/<int:classroom_pk>/teams/<int:pk>/add-members/', team_add_member_view, name='team-add-member'),
    path('api/classrooms/<int:classroom_pk>/teams/<int:pk>/remove-members/', team_remove_member_view, name='team-remove-member'),

    path('api/games/', game_list_create_view, name='game-list'),
    path('api/games/<int:pk>/', game_detail_view, name='game-detail'),
    path('api/games/<int:pk>/start/', game_start_view, name='game-start'),
    path('api/games/<int:pk>/pause/', game_pause_view, name='game-pause'),
    path('api/games/<int:pk>/advance-round/', game_advance_round_view, name='game-advance-round'),
    path('api/games/<int:game_pk>/parameters/', game_parameter_list_view, name='game-parameter-list'),
    path('api/games/<int:game_pk>/parameters/<int:pk>/', game_parameter_update_view, name='game-parameter-update'),

    path('api/games/<int:game_pk>/decisions/', decision_list_create_view, name='decision-list'),
    path('api/games/<int:game_pk>/decisions/<int:pk>/', decision_detail_view, name='decision-detail'),
    path('api/games/<int:game_pk>/my-decision/', my_decision_view, name='my-decision'),

    path('api/games/<int:game_pk>/dashboard/', dashboard_view, name='dashboard'),
    path('api/games/<int:game_pk>/ranking/', ranking_view, name='ranking'),
    path('api/games/<int:game_pk>/results/<int:round_number>/', round_result_view, name='round-result'),
    path('api/games/<int:game_pk>/trend/<int:team_pk>/', team_trend_view, name='team-trend'),
]
