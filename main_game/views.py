from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib.auth import authenticate, login, logout, get_user_model

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Torb, Colony, StoryText, Game
import logging
import json

logger = logging.getLogger(__name__)

@login_required
def colony_view(request, colony_id):
    try:
        colony = get_object_or_404(Colony, id=colony_id)
    except Http404:
        return redirect('main_page')
    
    torbs = colony.torb_set.all().order_by('private_ID')
    story_texts = StoryText.objects.filter(colony=colony).order_by('timestamp')
    
    if request.method == 'POST':
        selected_torbs = request.POST.getlist('selected_torbs')
        action = request.POST.get('action')
        
        if action == 'breed' and len(selected_torbs) == 2:
            colony.set_breed_torbs(selected_torbs)
        elif action == 'gather':
            for torb_id in selected_torbs:
                torb = Torb.objects.get(id=torb_id)
                torb.set_action("gathering", "🌾 Gathering")
        elif action == 'enlist':
            for torb_id in selected_torbs:
                torb = Torb.objects.get(id=torb_id)
                torb.set_action("training", "🎯 Training")
        elif action == 'end_turn':
            colony.ready_up()
        return redirect('colony_view', colony_id=colony.id)
    
    if torbs.exists():
        gene_names = list(torbs.first().genes.keys())
    else:
        gene_names = []
    logger.debug(f"Rendering colony_view with colony: {colony}, num_torbs: {colony.torb_count}, torbs: {torbs}, gene_names: {gene_names}, story_texts: {story_texts}")
    return render(request, 'main_game/colony.html', {
        'colony': colony,
        'num_torbs': colony.torb_count,
        'torbs': torbs,
        'gene_names': gene_names,
        'story_texts': story_texts,
        })

def check_ready_status(request, colony_id):
    colony = get_object_or_404(Colony, id=colony_id)
    return JsonResponse({'ready': colony.ready})

@login_required
def load_colony(request):
    user = request.user
    
    if request.method == 'POST':
        game_id = request.POST.get('game_id')
        colony_name = request.POST.get('colony_name')
        game = Game.objects.get(pk=game_id)
        if game and (not game.closed or user in game.allowed_players):
            Colony.objects.create(
                player=user,
                name=colony_name,
                game=game)
    
    colonies = Colony.objects.filter(player=user)
    games = Game.objects.filter(private=False) | Game.objects.filter(allowed_players__in=[user])
    return render(request, 'main_game/load_colony.html',
                  {'colonies': colonies,
                   'games': games})

def army_view(request, colony_id):
    colony = get_object_or_404(Colony, id=colony_id)
    torbs = colony.torb_set.all()
    num_soldiers = len([torb for torb in torbs if torb.action=="soldiering"])
    num_training = len([torb for torb in torbs if torb.action=="training"])
    known_colonies = colony.discovered_colonies.all().order_by('id')
    all_colonies = colony.game.colony_set.all().order_by('id')
    story_texts = StoryText.objects.filter(colony=colony).order_by('timestamp')
    
    if request.method == 'POST':
        selected_colony = request.POST.get('selected_colony')
        action = request.POST.get('action')
        
        if action == "scout":
            colony.army.set_scout_target(selected_colony)
        elif action == "attack":
            colony.army.set_attack_target(selected_colony)
        elif action == 'end_turn':
            colony.ready_up()

        
        return redirect('army_view', colony_id=colony.id)
    return render(request, 'main_game/army.html', {
        'colony': colony,
        'player_colony': colony,
        'story_texts': story_texts,
        'num_soldiers': num_soldiers,
        'num_training': num_training,
        'known_colonies': known_colonies,
        'all_colonies': all_colonies
        })
    
def main_page(request):
    if request.user.is_authenticated:
        return redirect('load_colony')
    return render(request, 'main_game/main_page.html')

class RegisterForm(UserCreationForm):
    usable_password = None
    class Meta:
        model = get_user_model()
        fields = ["username", "password1", "password2"]


def register(request):
    if request.user.is_authenticated:
        return redirect('load_colony')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('load_colony')
    else:
        form = RegisterForm()
    return render(request, 'main_game/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('load_colony')
    
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('load_colony')
    else:
        form = AuthenticationForm()
    
    return render(request, 'main_game/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('main_page')