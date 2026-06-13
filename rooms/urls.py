from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("create-room/", views.create_room_view, name='create_room'),
    path("join-room/", views.join_room_view, name="join_room"),
    path("<str:code>/", views.room_lobby_view, name="room_lobby"),
]