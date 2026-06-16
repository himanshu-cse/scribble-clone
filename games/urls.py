from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("start/<str:code>/", views.start_game_view, name='start_game'),
    path("<int:game_id>/", views.game_detail_view, name="game_detail"),
    path("<int:game_id>/end-round/", views.end_round_view, name="end_round"),
    path("<int:game_id>/test-guess/", views.test_guess_view, name="test_guess"),
]