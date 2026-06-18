from django.contrib import admin
from .models import Decision


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ['team', 'game', 'round_number', 'is_submitted', 'submitted_at']
    list_filter = ['is_submitted', 'game']
