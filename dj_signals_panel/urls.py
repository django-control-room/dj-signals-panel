from django.urls import path
from . import views

app_name = "dj_signals_panel"

urlpatterns = [
    path("", views.index, name="index"),
    path("detail/<path:signal_id>/", views.signal_detail, name="signal_detail"),
]
