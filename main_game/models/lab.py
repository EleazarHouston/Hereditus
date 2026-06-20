import logging
import random

from django.db import models
from django.db.models.functions import Now

from .story_text import StoryText

logger = logging.getLogger('hereditus')

class Lab(models.Model):
    colony = models.OneToOneField('Colony', on_delete=models.CASCADE, related_name='lab', null=True)
    science_points = models.IntegerField(default=0)
    discoveries = models.ManyToManyField('main_game.Discovery', related_name='labs', blank=True)
    mutagen = models.IntegerField(default=0, null=True, blank=True)
    
    def new_round(self):
        self.conduct_research()
    
    def conduct_research(self):
        science_contribution = 0
        for torb in self.colony.torbs.filter(action="researching"):
            intelligence = torb.genes.get('intelligence') or [0]
            science_contribution += 1 + int(random.choice(intelligence) * random.random())
        
        self.adjust_science_points(science_contribution)
        StoryText.objects.create(
            colony=self.colony,
            story_text_type="science",
            story_text=f"Your Torbs gleaned {science_contribution} science.",
            timestamp=Now())
    
    def adjust_science_points(self, adjust_amount):
        adjust_amount = int(adjust_amount)
        self.science_points = max(self.science_points + adjust_amount, 0)
        logger.debug(f"Adjusted science points by {adjust_amount} to {self.science_points} for Colony {self.colony}")
        self.save()
    
    def make_mutagen(self, science_points_used):
        science_points_used = int(science_points_used)
        if science_points_used < 10 or self.science_points < science_points_used:
            raise ValueError("Not enough science points to make mutagen.")
        
        self.science_points -= science_points_used
        mutagen_amount = max(int(science_points_used / 10),1)
        self.mutagen += mutagen_amount
        self.save()
        StoryText.objects.create(
            colony=self.colony,
            story_text_type="science",
            story_text=f"Your lab made {mutagen_amount} mutagen.",
            timestamp=Now())

    def unlock_discovery(self, discovery):
        if self.discoveries.filter(pk=discovery.pk).exists():
            raise ValueError("Discovery already unlocked.")
        if self.science_points < discovery.research_cost:
            raise ValueError("Not enough science points for this discovery.")

        self.science_points -= discovery.research_cost
        self.discoveries.add(discovery)
        self.save()
        StoryText.objects.create(
            colony=self.colony,
            story_text_type="science",
            story_text=f"Your lab unlocked '{discovery.name}'.",
            timestamp=Now())

class Discovery(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    research_cost = models.IntegerField(default=100)
