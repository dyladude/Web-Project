from django.contrib import admin
from .models import Todo, Service

@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "completed", "created_at")
    list_filter = ("completed",)
    search_fields = ("title", "owner__username")

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "check_type",
        "is_public",
        "last_status",
        "last_checked",
        "response_time_ms",
    )
    list_filter = ("check_type", "is_public", "last_status")
    search_fields = ("name", "description", "url", "heartbeat_token")