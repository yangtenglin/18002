from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'student_id', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('角色信息', {'fields': ('role', 'student_id', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('角色信息', {'fields': ('role', 'student_id', 'phone')}),
    )
