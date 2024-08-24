from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .torb_names import torb_names
import random

class Score(models.Model):
    value = models.IntegerField(default=0)
    
    def __str__(self):
        return str(self.value)

class Colony(models.Model):
    name = models.CharField(max_length=64, default="DefaultName")
    
    @property
    def torb_count(self):
        return self.torb_set.count()
    
    def new_torb(self):
        next_ID = self.torb_count + 1
        random.shuffle(torb_names)
        name = torb_names[0]
        Torb.objects.create(colony = self, private_ID=next_ID, name=name)

class Torb(models.Model):
    private_ID = models.IntegerField(default=0)
    name = models.CharField(max_length=16, default="Nonam")
    generation = models.IntegerField(default=0)
    colony = models.ForeignKey(Colony, on_delete=models.CASCADE)
    is_alive = models.BooleanField(default=True)
    health = models.IntegerField(default=10)
    
    

