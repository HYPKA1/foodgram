from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Subscription, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Настройка пользователей в админ-панели."""

    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
    )

    search_fields = (
        'username',
        'email',
    )

    list_filter = (
        'is_staff',
        'is_superuser',
        'is_active',
    )

    ordering = ('id',)

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('avatar',),
        }),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Управление подписками пользователей."""

    list_display = (
        'id',
        'user',
        'author',
    )

    search_fields = (
        'user__username',
        'author__username',
    )
