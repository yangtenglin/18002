from django.contrib import admin
from .models import Game, GameParameter


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_room', 'status', 'current_round', 'total_rounds', 'created_at']
    list_filter = ['status']
    search_fields = ['name']


@admin.register(GameParameter)
class GameParameterAdmin(admin.ModelAdmin):
    list_display = ['game', 'round_number', 'market_base_demand', 'seasonal_factor', 'economic_factor']
    list_filter = ['game']
