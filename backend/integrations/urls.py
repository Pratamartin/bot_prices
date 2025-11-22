from django.urls import path
from . import views

urlpatterns = [
    path("auth/start", views.ml_auth_start, name="ml_auth_start"),
    path("auth/callback", views.ml_auth_callback, name="ml_auth_callback"),
    path("notifications/", views.ml_notifications, name="ml_notifications"),
]
