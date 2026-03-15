import json
import time
import urllib.request
import urllib.error

from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .models import Todo, Service
from .forms import TodoForm

class TodoListView(LoginRequiredMixin, ListView):
    model = Todo
    template_name = "core/todo_list.html"
    context_object_name = "todos"

    def get_queryset(self):
        return Todo.objects.filter(owner=self.request.user)

class TodoCreateView(LoginRequiredMixin, CreateView):
    model = Todo
    form_class = TodoForm
    template_name = "core/todo_form.html"
    success_url = reverse_lazy("todo-list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

class TodoUpdateView(LoginRequiredMixin, UpdateView):
    model = Todo
    form_class = TodoForm
    template_name = "core/todo_form.html"
    success_url = reverse_lazy("todo-list")

    def get_queryset(self):
        return Todo.objects.filter(owner=self.request.user)

class TodoDeleteView(LoginRequiredMixin, DeleteView):
    model = Todo
    template_name = "core/todo_confirm_delete.html"
    success_url = reverse_lazy("todo-list")

    def get_queryset(self):
        return Todo.objects.filter(owner=self.request.user)

def resume(request):
    return render(request, "core/resume.html")

def dashboard(request):
    services = Service.objects.all()
    return render(request, "core/dashboard.html", {"services": services})


def health(request):
    return JsonResponse({"status": "ok"})


@csrf_exempt
def heartbeat(request, token):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    service = get_object_or_404(Service, heartbeat_token=token, check_type=Service.CHECK_PUSH)

    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    status = data.get("status", Service.STATUS_UNKNOWN)
    response_time_ms = data.get("response_time_ms")

    if status not in {Service.STATUS_UP, Service.STATUS_DOWN, Service.STATUS_UNKNOWN}:
        status = Service.STATUS_UNKNOWN

    service.last_status = status
    service.last_checked = timezone.now()
    service.response_time_ms = response_time_ms if isinstance(response_time_ms, int) else None
    service.save(update_fields=["last_status", "last_checked", "response_time_ms"])

    return JsonResponse({"ok": True, "service": service.name})

@login_required
def run_pull_checks(request):
    services = Service.objects.filter(check_type=Service.CHECK_PULL, is_public=True)
    results = []

    for service in services:
        start = time.monotonic()
        status = Service.STATUS_DOWN
        response_time_ms = None

        try:
            with urllib.request.urlopen(service.url, timeout=5) as response:
                elapsed = (time.monotonic() - start) * 1000
                response_time_ms = int(elapsed)
                if 200 <= response.status < 400:
                    status = Service.STATUS_UP
        except (urllib.error.URLError, ValueError):
            status = Service.STATUS_DOWN

        service.last_status = status
        service.last_checked = timezone.now()
        service.response_time_ms = response_time_ms
        service.save(update_fields=["last_status", "last_checked", "response_time_ms"])

        results.append({
            "name": service.name,
            "status": service.last_status,
            "response_time_ms": service.response_time_ms,
        })

    return JsonResponse({"checked": len(results), "results": results})
