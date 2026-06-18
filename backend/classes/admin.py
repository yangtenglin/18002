from django.contrib import admin
from .models import ClassRoom, Team


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'teacher', 'is_active', 'created_at']
    list_filter = ['is_active', 'teacher']
    search_fields = ['name', 'code']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'class_room', 'captain', 'created_at']
    list_filter = ['class_room']
    search_fields = ['name']
