from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .torb_names import torb_names
import random

class Score(models.Model):
    value = models.IntegerField(default=0)
    
    def __str__(self):
        return str(self.value)

class Game(models.Model):
    starting_torbs = models.IntegerField(default=4)
    description = models.CharField(max_length=256, null=True)
    
    def __str__(self):
        return self.description
    
    
    

class Colony(models.Model):
    name = models.CharField(max_length=64, default="DefaultName")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True)
    
    
    @property
    def torb_count(self):
        return self.torb_set.count()
    
    def new_torb(self):
        next_ID = self.torb_count + 1
        random.shuffle(torb_names)
        name = torb_names[0]
        Torb.objects.create(colony = self, private_ID=next_ID, name=name)
        
    def init_torbs(self):
        for i in range(self.game.starting_torbs):
            self.new_torb()
        
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.init_torbs()
        

class Torb(models.Model):
    private_ID = models.IntegerField(default=0)
    name = models.CharField(max_length=16, default="Nonam")
    generation = models.IntegerField(default=0)
    colony = models.ForeignKey(Colony, on_delete=models.CASCADE)
    is_alive = models.BooleanField(default=True)
    health = models.IntegerField(default=10)
    
    

