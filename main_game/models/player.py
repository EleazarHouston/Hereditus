import logging
import random

from django.db import models
from django.contrib.auth.models import User

from polymorphic.models import PolymorphicModel

from .torb import Torb

logger = logging.getLogger('hereditus')

class Player(PolymorphicModel):
    name = models.CharField(max_length=255)
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE, related_name='players')
    polymorphic_ctype = models.ForeignKey(
        'contenttypes.ContentType',
        editable=False,
        null=True,
        on_delete=models.CASCADE,
        related_name='polymorphic_%(app_label)s.%(class)s_set+'
    )
    
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

    def __str__(self):
        return f"Player {self.name}"
    
class AIPlayer(Player):
    difficulty = models.IntegerField(default=10)
    
    def make_decisions(self, colony):
        # Get a queryset of Torbs that are gathering
        gathering_torbs = colony.torbs.filter(action="gathering")
        # List to keep track of Torbs that have been assigned an important action
        important_torbs = []
        
        # Breeding
        if colony.food > 5 and colony.food > colony.torb_count // 2:
            num_breeding_pairs = int(colony.torb_count ** 0.5)
            logger.debug(f"AIPlayer {self} is breeding {num_breeding_pairs} pairs of random Torbs")
            for _ in range(num_breeding_pairs):
                # Select two random torbs that are gathering for breeding
                torb_ids = list(gathering_torbs.order_by('?')[:2].values_list('id', flat=True))
                gathering_torbs = gathering_torbs.exclude(id__in=torb_ids)
                important_torbs.extend(torb_ids)
                self.perform_action(colony, action='breed', torb_ids=torb_ids)
        
        # Enlisting soldiers
        if colony.torb_count > 6 and colony.food >= 5:
            # Determine the number of torbs to enlist
            desired_army_size = max(1, colony.torb_count // random.randint(6, 10))
            current_army_size = colony.torbs.filter(action="training").count()
            num_to_enlist = desired_army_size - current_army_size
            
            if num_to_enlist > 0:
                # Select random torbs that are gathering for enlisting
                logger.debug(f"AIPlayer {self} is enlisting {num_to_enlist} random Torbs")
                torb_ids = list(gathering_torbs.order_by('?')[:num_to_enlist].values_list('id', flat=True))
                important_torbs.extend(torb_ids)
                gathering_torbs = gathering_torbs.exclude(id__in=torb_ids)
                self.perform_action(colony, action='enlist', torb_ids=torb_ids)
        
        # Scouting
        if colony.torbs.filter(action="soldiering").exists():
            undiscovered_colonies = colony.game.colony_set.exclude(id__in=colony.discovered_colonies.all())
            if undiscovered_colonies.exists():
                target_colony = undiscovered_colonies.order_by('?').first()
                logger.debug(f"AIPlayer {self} is scouting colony {target_colony}")
                self.perform_action(colony, action='scout', target_colony_id=target_colony.id)
        
        # Attacking
        soldiers = colony.torbs.filter(action="soldiering")
        if soldiers.exists() and all(torb.hp == torb.max_hp for torb in soldiers):
            enemy_colonies = colony.discovered_colonies.exclude(player=self)
            if enemy_colonies.exists():
                target_colony = enemy_colonies.order_by('?').first()
                logger.debug(f"AIPlayer {self} is attacking colony {target_colony}")
                self.perform_action(colony, action='attack', target_colony_id=target_colony.id)
        
        self.perform_action(colony, action='end_turn')