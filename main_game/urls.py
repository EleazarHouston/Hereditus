from django.urls import path
from .views import torb_view_attempt, colony_view, check_ready_status

urlpatterns = [
    path('play/torb', torb_view_attempt, name='Look at a Torb'),
    path('play/', colony_view, name='colony_view'),
    path('check_ready_status/', check_ready_status, name='check_ready_status')
]
