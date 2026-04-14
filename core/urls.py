from django.urls import path

from .views import TodoCreateView, TodoDeleteView, TodoListView, TodoUpdateView

urlpatterns = [
    path("", TodoListView.as_view(), name="todo-list"),
    path("new/", TodoCreateView.as_view(), name="todo-create"),
    path("<int:pk>/edit/", TodoUpdateView.as_view(), name="todo-update"),
    path("<int:pk>/delete/", TodoDeleteView.as_view(), name="todo-delete"),
]