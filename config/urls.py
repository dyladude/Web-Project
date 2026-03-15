"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from core.views import resume, dashboard, health, heartbeat, run_pull_checks


urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("todos/", include("core.urls")),
    path("resume/", resume, name="resume"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("health/", health, name="health"),
    path("health/run/", run_pull_checks, name="run-pull-checks"),
    path("health/heartbeat/<str:token>/", heartbeat, name="heartbeat"),
]