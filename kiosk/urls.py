from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("start_detect/", views.start_detect, name="start_detect"),
    path("live_cam/", views.live_cam, name="live_cam"),
    path("result/", views.result, name="result")
]
