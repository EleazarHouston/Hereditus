from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('play/<int:colony_id>/overview/', views.colony_view, name='colony_view'),
    path('play/<int:colony_id>/army/', views.army_view, name='army_view'),
    path('check_ready_status/<int:colony_id>/', views.check_ready_status, name='check_ready_status'),
    path('load_colony/', views.load_colony, name='load_colony'),
    path('register/', views.register, name='register'),
    path('login', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('play/<int:colony_id>/settings/', views.settings_view, name='settings_view'),
    path('play/<int:colony_id>/science/', views.science_view, name='science_view')
]

# Error when accessing colony URL when not logged in