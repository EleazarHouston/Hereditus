import logging

from django.contrib.auth.models import User
from django.db import models

from .player import AIPlayer

logger = logging.getLogger('hereditus')

class Game(models.Model):
    starting_torbs = models.IntegerField(default=4)
    description = models.CharField(max_length=256, null=True)
    round_number = models.IntegerField(default=1)
    private = models.BooleanField(default=False)
    allowed_players = models.ManyToManyField(User, blank=True)
    closed = models.BooleanField(default=False)
    max_colonies_per_player = models.IntegerField(default=1)
    
    def __str__(self):
        return self.description
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"A new Game '{self.description}' was made")
            from .evolution_engine import EvolutionEngine
            EvolutionEngine.objects.create(game=self)
            
    @property
    def unready_colonies(self):
        return self.colony_set.filter(ready=False).count()
    
    def next_round(self):
        for colony in self.colony_set.all().order_by('?'):
            colony.new_round(round_number = self.round_number)
            
        # Done in a separate loop because web GUIs are updated when ready value is updated
        for colony in self.colony_set.all():
            colony.ready = False
            colony.save()
        self.round_number += 1
        self.save()
        logger.debug(f"Next round processed successfully")
        self.run_ai_players()
    
    def run_ai_players(self):
        ai_colonies = self.colony_set.filter(player__user__isnull=True)
        print(ai_colonies)
        for colony in ai_colonies:
            cur_player = colony.player
            print(isinstance(cur_player, AIPlayer))
            colony.player.make_decisions(colony)
    
    def check_ready_status(self):
        logger.debug(f"Checking colonies ready statuses")
        if self.colony_set.filter(ready=False).count() >= 1:
            return False
        logger.debug(f"All colonies are ready for the next round")
        self.next_round()