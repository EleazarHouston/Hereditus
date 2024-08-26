from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Torb, Colony, StoryText
import logging

logger = logging.getLogger(__name__)

# Create your views here.


def torb_view_attempt(request):
    torb = get_object_or_404(Torb, id=1)
    
    return render(request, 'main_game/torb.html', {'private_id': torb.private_ID , 'health': torb.health})

def colony_view(request, colony_id):
    colony = get_object_or_404(Colony, id=colony_id)
        
    torbs = colony.torb_set.all().order_by('private_ID')
    story_texts = StoryText.objects.filter(colony=colony).order_by('timestamp')
    
    if request.method == 'POST':
        selected_torbs = request.POST.getlist('selected_torbs')
        action = request.POST.get('action')
        print(len(selected_torbs))
        
        if action == 'breed' and len(selected_torbs) == 2:
            # Should probably be moved to a colony method
            torb0 = Torb.objects.get(id=selected_torbs[0])
            torb1 = Torb.objects.get(id=selected_torbs[1])
            torb0.action = "breeding"
            torb0.context_torb = torb1
            torb0.action_desc = f"Breeding with {torb1.name}"
            torb0.save()
            
            torb1.action = "breeding"
            torb1.context_torb = torb0
            torb1.action_desc = f"Breeding with {torb0.name}"
            torb1.save()
            #colony.game.evolution_engine.breed_torbs(colony=colony, torb0=torb0, torb1=torb1)
        elif action == 'gather':
            pass
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

def check_ready_status(request):
    colony = Colony.objects.order_by('id').first()
    return JsonResponse({'ready': colony.ready})

def load_colony(request):
    colonies = Colony.objects.all()
    return render(request, 'main_game/load_colony.html', {'colonies': colonies})