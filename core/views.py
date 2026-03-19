import base64
import json
import time
import urllib.request
import urllib.error

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotAllowed,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .forms import TodoForm
from .models import Service, Todo

User = get_user_model()


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


# ---------- Basic auth helpers ----------

def _unauthorized(message="Authentication required"):
    response = JsonResponse({"detail": message}, status=401)
    response["WWW-Authenticate"] = 'Basic realm="Web Project API"'
    return response


def _parse_basic_auth(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Basic "):
        return None

    encoded = header.split(" ", 1)[1].strip()
    try:
        decoded = base64.b64decode(encoded).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None

    if ":" not in decoded:
        return None

    username, password = decoded.split(":", 1)
    user = authenticate(request, username=username, password=password)
    return user


def require_basic_auth(view_func):
    def wrapped(request, *args, **kwargs):
        user = _parse_basic_auth(request)
        if user is None:
            return _unauthorized()
        request.basic_user = user
        return view_func(request, *args, **kwargs)

    wrapped.__name__ = getattr(view_func, "__name__", "wrapped")
    return wrapped


def _forbidden(message="Forbidden"):
    return JsonResponse({"detail": message}, status=403)


def _service_to_dict(service):
    return {
        "id": service.id,
        "name": service.name,
        "description": service.description,
        "url": service.url,
        "check_type": service.check_type,
        "is_public": service.is_public,
        "last_status": service.last_status,
        "last_checked": service.last_checked.isoformat() if service.last_checked else None,
        "response_time_ms": service.response_time_ms,
    }


def _user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "is_staff": user.is_staff,
        "role": "admin" if user.is_staff else "author",
        "is_active": user.is_active,
    }


def _load_json(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return None


# ---------- HTML views ----------

def resume(request):
    return render(request, "core/resume.html")


def dashboard(request):
    return render(request, "core/dashboard.html")


def health(request):
    return JsonResponse({"status": "ok"})


@csrf_exempt
def heartbeat(request, token):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    service = get_object_or_404(Service, heartbeat_token=token, check_type=Service.CHECK_PUSH)

    data = _load_json(request)
    if data is None:
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


# ---------- API views ----------

@csrf_exempt
def api_services(request):
    if request.method == "GET":
        services = Service.objects.filter(is_public=True)
        return JsonResponse({"services": [_service_to_dict(s) for s in services]})

    if request.method == "POST":
        return api_service_create(request)

    return HttpResponseNotAllowed(["GET", "POST"])


@require_basic_auth
@csrf_exempt
def api_service_create(request):
    data = _load_json(request)
    if data is None:
        return HttpResponseBadRequest("Invalid JSON")

    service = Service.objects.create(
        name=data.get("name", "").strip(),
        description=data.get("description", "").strip(),
        url=data.get("url", "").strip(),
        check_type=data.get("check_type", Service.CHECK_PULL),
        is_public=bool(data.get("is_public", True)),
    )

    if not service.name:
        service.delete()
        return HttpResponseBadRequest("Name is required")

    if service.check_type not in {Service.CHECK_PULL, Service.CHECK_PUSH}:
        service.check_type = Service.CHECK_PULL
        service.save(update_fields=["check_type"])

    return JsonResponse(_service_to_dict(service), status=201)


@csrf_exempt
def api_service_detail(request, pk):
    if request.method == "PUT":
        return api_service_update(request, pk)
    if request.method == "DELETE":
        return api_service_delete(request, pk)
    return HttpResponseNotAllowed(["PUT", "DELETE"])


@require_basic_auth
@csrf_exempt
def api_service_update(request, pk):
    service = get_object_or_404(Service, pk=pk)
    data = _load_json(request)
    if data is None:
        return HttpResponseBadRequest("Invalid JSON")

    for field in ["name", "description", "url", "check_type", "is_public", "last_status", "response_time_ms"]:
        if field in data:
            setattr(service, field, data[field])

    if data.get("touch_checked"):
        service.last_checked = timezone.now()

    if service.check_type not in {Service.CHECK_PULL, Service.CHECK_PUSH}:
        return HttpResponseBadRequest("Invalid check_type")

    if service.last_status not in {Service.STATUS_UP, Service.STATUS_DOWN, Service.STATUS_UNKNOWN}:
        service.last_status = Service.STATUS_UNKNOWN

    service.save()
    return JsonResponse(_service_to_dict(service))


@require_basic_auth
@csrf_exempt
def api_service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    service.delete()
    return JsonResponse({"deleted": pk})


@csrf_exempt
@require_basic_auth
def api_users(request):
    user = request.basic_user

    if request.method == "GET":
        users = User.objects.order_by("username")
        return JsonResponse({"users": [_user_to_dict(u) for u in users], "viewer": _user_to_dict(user)})

    if request.method == "POST":
        if not user.is_staff:
            return _forbidden("Only admins can create credentials")

        data = _load_json(request)
        if data is None:
            return HttpResponseBadRequest("Invalid JSON")

        username = (data.get("username") or "").strip()
        password = data.get("password") or ""
        role = data.get("role", "author")

        if not username or not password:
            return HttpResponseBadRequest("Username and password are required")
        if User.objects.filter(username=username).exists():
            return HttpResponseBadRequest("Username already exists")

        new_user = User.objects.create_user(
            username=username,
            password=password,
            is_staff=(role == "admin"),
        )
        return JsonResponse(_user_to_dict(new_user), status=201)

    return HttpResponseNotAllowed(["GET", "POST"])


@csrf_exempt
@require_basic_auth
def api_user_detail(request, pk):
    actor = request.basic_user
    target = get_object_or_404(User, pk=pk)

    if request.method == "PUT":
        if not actor.is_staff:
            return _forbidden("Only admins can update credentials")

        data = _load_json(request)
        if data is None:
            return HttpResponseBadRequest("Invalid JSON")

        if "password" in data and data["password"]:
            target.set_password(data["password"])
        if "role" in data:
            target.is_staff = data["role"] == "admin"
        if "is_active" in data:
            target.is_active = bool(data["is_active"])
        target.save()
        return JsonResponse(_user_to_dict(target))

    if request.method == "DELETE":
        if not actor.is_staff:
            return _forbidden("Only admins can delete credentials")
        if actor.pk == target.pk:
            return _forbidden("Admins cannot delete themselves from this interface")
        target.delete()
        return JsonResponse({"deleted": pk})

    return HttpResponseNotAllowed(["PUT", "DELETE"])
