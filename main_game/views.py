from django.shortcuts import render, redirect, get_object_or_404
from .models import Score, Torb, Colony

# Create your views here.
def score_view(request):
    score, created = Score.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        score.value += 1
        score.save()
        return redirect('score_page')
    
    return render(request, 'main_game/score.html', {'score': score})

def torb_view_attempt(request):
    torb = get_object_or_404(Torb, id=1)
    
    return render(request, 'main_game/torb.html', {'private_id': torb.private_ID , 'health': torb.health})

def colony_view(request):
    colony = Colony.objects.order_by('id').first()
    torbs = colony.torb_set.all().order_by('private_ID')
    
    if request.method == 'POST':
        selected_torbs = request.POST.getlist('selected_torbs')
        action = request.POST.get('action')
        
        if action == 'breed' and len(selected_torbs) == 2:
            torb0 = Torb.objects.get(id=selected_torbs[0])
            torb1 = Torb.objects.get(id=selected_torbs[1])
            colony.game.evolution_engine.breed_torbs(colony=colony, torb0=torb0, torb1=torb1)
        elif action == 'gather':
            pass
        elif action == 'end_turn':
            colony.ready = True
            colony.save()
        
        return redirect('colony_view')
    
    
    
    if torbs.exists():
        gene_names = list(torbs.first().genes.keys())
    else:
        gene_names = []
    
    return render(request, 'main_game/colony.html', {
        'colony': colony,
        'num_torbs': colony.torb_count,
        'torbs': torbs,
        'gene_names': gene_names,
        })
    