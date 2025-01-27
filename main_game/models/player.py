import logging
from django.db import models
from django.contrib.auth.models import User

from .torb import Torb

logger = logging.getLogger('hereditus')

class Player(models.Model):
    name = models.CharField(max_length=255)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE, related_name='players')
    
    @property
    def is_human(self):
        return self.user is not None
    
    def save(self, *args, **kwargs):
        if not self.pk and self.user:
            self.name = self.user.username
        super().save(*args, **kwargs)
    
    def get_colonies(self):
        return self.colony_set.all()
    
    def perform_action(self, colony, action, **kwargs):
        if colony.player != self:
            logger.warning(f"Player {self} attempted to perform action on colony {colony} which they do not own.")
        
        if action == 'breed':
            colony.set_breed_torbs(kwargs.get('torb_ids'))
        elif action == 'gather':
            colony.assign_torbs_action(torb_ids=kwargs.get('torb_ids'), action="gathering")
        elif action == 'enlist':
            colony.assign_torbs_action(torb_ids=kwargs.get('torb_ids'), action="training")
        elif action == 'scout':
            target_colony_id = kwargs.get('target_colony_id')
            colony.army.set_scout_target(target_colony_id)
        elif action == 'attack':
            target_colony_id = kwargs.get('target_colony_id')
            colony.army.set_attack_target(target_colony_id)
        elif action == 'end_turn':
            colony.ready_up()
        else:
            raise ValueError(f"Unknown action: {action}")
    
    def breed_torbs(self, colony, torbs):
        if len(torbs) == 2:
            colony.set_breed_torbs(torbs)
        else:
            raise ValueError("Invalid number of Torbs to breed. Needs exactly two.")
            
    def assign_torbs_action(self, torbs, action):
        for torb in torbs:
            torb.set_action(action=action)
            
    def __str__(self):
        return f"Player {self.name}"
    
class AIPlayer(Player):
    difficulty = models.IntegerField(default=10)
    
    def ai_logic(self):
        pass