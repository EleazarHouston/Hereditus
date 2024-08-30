from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Torb, Colony, StoryText
import logging
import json

logger = logging.getLogger(__name__)

# Create your views here.


def torb_view_attempt(request):
    torb = get_object_or_404(Torb, id=1)
    
    return render(request, 'main_game/torb.html', {'private_id': torb.private_ID , 'health': torb.health})

def colony_view(request, colony_id):
    colony = get_object_or_404(Colony, id=colony_id)
    colony.discovered_colonies.add(colony)
        
    torbs = colony.torb_set.all().order_by('private_ID')
    story_texts = StoryText.objects.filter(colony=colony).order_by('timestamp')
    
    if request.method == 'POST':
        selected_torbs = request.POST.getlist('selected_torbs')
        action = request.POST.get('action')
        
        print(f"POST ACTION: {action}")
        if action == 'breed' and len(selected_torbs) == 2:
            colony.set_breed_torbs(selected_torbs)
            
        elif action == 'gather':
            for torb_id in selected_torbs:
                torb = Torb.objects.get(id=torb_id)
                torb.set_action("gathering", "Gathering")
        elif action == 'enlist':
            for torb_id in selected_torbs:
                torb = Torb.objects.get(id=torb_id)
                torb.set_action("training", "Training")
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

def load_colony(request):
    colonies = Colony.objects.all()
    return render(request, 'main_game/load_colony.html', {'colonies': colonies})

def army_view(request, colony_id):
    colony = get_object_or_404(Colony, id=colony_id)
    torbs = colony.torb_set.all()
    num_soldiers = len([torb for torb in torbs if torb.action=="soldiering"])
    num_training = len([torb for torb in torbs if torb.action=="training"])
    known_colonies = colony.discovered_colonies.all()
    story_texts = StoryText.objects.filter(colony=colony).order_by('timestamp')
    return render(request, 'main_game/army.html', {
        'colony': colony,
        'story_texts': story_texts,
        'num_soldiers': num_soldiers,
        'num_training': num_training,
        'known_colonies': known_colonies
        })