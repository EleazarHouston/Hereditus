from django.db import models
from django.apps import apps
import random
import logging
from django.db.models.functions import Now

logger = logging.getLogger('hereditus')

class Torb(models.Model):
    
    TORB_ACTION_OPTIONS = [
        ('gathering', 'gathering'),
        ('breeding', 'breeding'),
        ('soldiering', 'soldiering'),
        ('training', 'training'),
        ('resting', 'resting'),
        ('growing', 'growing'),
    ]
    
    private_ID = models.IntegerField(default=0)
    name = models.CharField(max_length=16, default="Nonam")
    generation = models.IntegerField(default=0)
    colony = models.ForeignKey('main_game.Colony', on_delete=models.CASCADE, related_name='torbs')
    is_alive = models.BooleanField(default=True)
    hp = models.IntegerField(default=5)
    max_hp = models.IntegerField(default=5)
    fertile = models.BooleanField(default=True)
    starving = models.BooleanField(default=False)
    action = models.CharField(max_length=32, choices=TORB_ACTION_OPTIONS, default='gathering',)
    action_desc = models.CharField(max_length=256, default='🌾 Gathering')
    context_torb = models.ForeignKey("Torb", null=True, blank=True, on_delete=models.SET_NULL)
    growing = models.BooleanField(default=False)
    trained = models.BooleanField(default=False)
    genes = models.JSONField(default=dict)
    army = models.ForeignKey('main_game.Army', on_delete=models.SET_NULL, null=True, blank=True)

    TORB_ACTIONS = {
        'gathering': '🌾 Gathering',
        'growing': '🍼 Growing',
        'dead': '💀 Dead',
        'soldiering': '🏹 Soldiering',
        'breeding': '💦 Breeding',
        'training': '🎯 Training',
    }

    @property
    def power(self):
        strength_allele = random.choice(self.genes['strength'])
        agility_allele = random.choice(self.genes['agility'])
        power = round((strength_allele * agility_allele)**0.5,2)
        return power
    
    @property
    def resilience(self):
        vitality_allele = random.choice(self.genes['vitality'])
        sturdiness_allele = random.choice(self.genes['sturdiness'])
        resilience = round((vitality_allele * sturdiness_allele)**0.5,2)
        return resilience
    
    def __str__(self):
        return f"Colony {self.colony} Torb: {self.private_ID} '{self.name}'"
    
    def adjust_hp(self, adjust_amount, context="an unknown source"):
        # TODO: Only log if Torb hp actually changes
        logger.debug(f"Colony {self.colony.id} '{self.colony.name}' Torb {self.private_ID} '{self.name}' adjusted hp amt {adjust_amount} context: {context}")
        adjust_amount = int(adjust_amount)
        from .story_text import StoryText
        self.hp = min(max(0, self.hp + adjust_amount), self.max_hp)
        if self.hp > 0:
            self.save()
            return
        self.is_alive = False
        self.fertile = False
        StoryText.objects.create(
            colony=self.colony,
            story_text_type="death",
            story_text=f"'{self.name}' (Torb {self.private_ID}) died from {context}.",
            timestamp=Now())
        logger.debug(f"Colony {self.colony.id} '{self.colony.name}' Torb {self.private_ID} '{self.name}' died, context: {context}")
        self.save()
        self.set_action(action="dead")
        if self.army_torb.first():
            self.army_torb.first().remove_from_army()
        
    def set_action(self, action: str, context_torb=None):
        if not self.is_alive:
            self.action = "dead"
            self.action_desc = self.TORB_ACTIONS['dead']
            self.save()
            return
        
        if self.growing:
            self.action = "growing"
            self.action_desc = self.TORB_ACTIONS['growing']
            self.save()
            return
        
        logger.debug(f"Colony {self.colony.id} '{self.colony.name}' Torb {self.private_ID} setting action {action} context torb: {context_torb}")
        # If prior action was breeding, ensure paired torb is also no longer breeding
        if self.action == "breeding" and self.context_torb:
            logger.debug(f"Colony {self.colony.id} '{self.colony.name}' Torb {self.private_ID} Already breeding with {self.context_torb}")
            self.context_torb.context_torb = None
            self.context_torb.action = "gathering"
            self.context_torb.action_desc = self.TORB_ACTIONS['gathering']
            self.context_torb.save()
        
        self.action = action
        if action == 'breeding' and context_torb:
            self.action_desc = f"💦 Breeding with {context_torb.name}"
        else:
            self.action_desc = self.TORB_ACTIONS.get(action, 'Unknown Action')
        self.context_torb = context_torb
        self.save()
    
    @property
    def status(self):
        out_text = ""
        if not self.is_alive:
            out_text += "Dead"
        elif self.starving:
            out_text += "Starving"
        else:
            out_text += "Alive"
            
        # Use <br> for HTML newline
        if self.fertile:
            out_text += "<br>Fertile"
        else:
            out_text += "<br>Infertile"
        
        if self.growing:
            out_text += "<br>Juvenile"
        
        return out_text