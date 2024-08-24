from django.urls import path
from .views import score_view, torb_view_attempt, colony_view

urlpatterns = [
    path('score', score_view, name='score_page'),
    path('play/torb', torb_view_attempt, name='Look at a Torb'),
    path('play/', colony_view, name='colony_view')
]
