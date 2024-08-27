from django.urls import path
from . import views

urlpatterns = [
    path('play/torb', views.torb_view_attempt, name='Look at a Torb'),
    path('play/<int:colony_id>/overview/', views.colony_view, name='colony_view'),
    path('play/<int:colony_id>/army/', views.army_view, name='army_view'),
    path('check_ready_status/<int:colony_id>/', views.check_ready_status, name='check_ready_status'),
    path('load_colony/', views.load_colony, name='load_colony')
]
