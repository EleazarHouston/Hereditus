from django.urls import path
from . import views

urlpatterns = [
    path('play/torb', views.torb_view_attempt, name='Look at a Torb'),
    path('play/<int:colony_id>/', views.colony_view, name='colony_view'),
    path('check_ready_status/', views.check_ready_status, name='check_ready_status'),
    path('load_colony/', views.load_colony, name='load_colony')
]
