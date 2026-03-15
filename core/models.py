from django.conf import settings
from django.db import models


class Todo(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="todos")
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["completed", "-created_at"]

    def __str__(self):
        return self.title


class Service(models.Model):
    CHECK_PULL = "pull"
    CHECK_PUSH = "push"

    CHECK_TYPE_CHOICES = [
        (CHECK_PULL, "Pull"),
        (CHECK_PUSH, "Push"),
    ]

    STATUS_UP = "up"
    STATUS_DOWN = "down"
    STATUS_UNKNOWN = "unknown"

    STATUS_CHOICES = [
        (STATUS_UP, "Up"),
        (STATUS_DOWN, "Down"),
        (STATUS_UNKNOWN, "Unknown"),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    check_type = models.CharField(max_length=10, choices=CHECK_TYPE_CHOICES, default=CHECK_PULL)
    is_public = models.BooleanField(default=True)
    last_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_UNKNOWN)
    last_checked = models.DateTimeField(null=True, blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)

    # only needed for push checks
    heartbeat_token = models.CharField(max_length=64, blank=True, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
