from django.contrib import admin
from .models import RoundResult, CumulativeResult


@admin.register(RoundResult)
class RoundResultAdmin(admin.ModelAdmin):
    list_display = ['team', 'game', 'round_number', 'profit', 'customer_satisfaction', 'score']
    list_filter = ['game']


@admin.register(CumulativeResult)
class CumulativeResultAdmin(admin.ModelAdmin):
    list_display = ['team', 'game', 'total_profit', 'final_score', 'rank']
    list_filter = ['game']
