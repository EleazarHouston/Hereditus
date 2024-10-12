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
    colony = models.ForeignKey('main_game.Colony', on_delete=models.CASCADE)
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
        from .story_text import StoryText
        self.hp = min(max(0, self.hp + adjust_amount), self.max_hp)
        if self.hp == 0:
            self.is_alive = False
            self.fertile = False
            StoryText.objects.create(colony=self.colony, story_text_type="death", story_text=f"'{self.name}' (Torb {self.private_ID}) died from {context}.", timestamp=Now())
            logger.debug(f"Colony {self.colony.id} '{self.colony.name}' Torb {self.private_ID} '{self.name}' died, context: {context}")
        self.save()
        
    def set_action(self, action: str, action_desc: str, context_torb=None):
        if self.growing:
            self.action = "growing"
            self.action_desc = "🍼 Growing"
            self.save()
            return
        self.action = action
        self.action_desc = action_desc
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
        