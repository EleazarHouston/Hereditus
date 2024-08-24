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
    colony, created = Colony.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        Colony.new_torb(colony)
        
    torbs = colony.torb_set.all()
    
    return render(request, 'main_game/colony.html', {
        'colony_name': colony.name,
        'num_torbs': colony.torb_count,
        'torbs': torbs})
    