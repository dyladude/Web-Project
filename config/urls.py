from django.contrib import admin
from django.urls import include, path

from core.views import (
    api_service_detail,
    api_services,
    api_user_detail,
    api_users,
    dashboard,
    health,
    heartbeat,
    resume,
    run_pull_checks,
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("todos/", include("core.urls")),
    path("resume/", resume, name="resume"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("health/", health, name="health"),
    path("health/run/", run_pull_checks, name="run-pull-checks"),
    path("health/heartbeat/<str:token>/", heartbeat, name="heartbeat"),
    path("api/services/", api_services, name="api-services"),
    path("api/services/<int:pk>/", api_service_detail, name="api-service-detail"),
    path("api/users/", api_users, name="api-users"),
    path("api/users/<int:pk>/", api_user_detail, name="api-user-detail"),
]
