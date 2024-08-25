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
    evolution_engine = models.OneToOneField('EvolutionEngine', on_delete=models.CASCADE, null=True, blank=True, related_name='game_instance')
    
    def __str__(self):
        return self.description
    
def default_gene_list():
    return ["health", "defense", "agility", "strength"]

def default_gene_alleles():
    return ['5', '5']

class EvolutionEngine(models.Model):
    game = models.OneToOneField(Game, on_delete=models.CASCADE, related_name='evolution_engine_instance')
    random_gene_min = models.IntegerField(default=1)
    random_gene_max = models.IntegerField(default=10)
    mutation_chance = models.FloatField(default=0.1)
    mutation_dev = models.FloatField(default=0.15)
    alleles_per_gene = models.IntegerField(default=2)
    gene_list = models.JSONField(default=default_gene_alleles)
    
    def check_torb_breedable(self, torb):
        if not torb.fertile:
            return False
        return True
    
    def breed_torbs(self, torb1, torb2):
        if not self.check_torb_breedable(torb1) or not self.check_torb_breedable(torb2):
            return False
        for j, gene in enumerate(self.gene_list):
            print(gene)

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
    TORB_ACTION_OPTIONS = [
        ('gathering', 'gathering'),
        ('breeding', 'breeding'),
        ('combatting', 'combatting'),
        ('training', 'training'),
        ('resting', 'resting'),
    ]
    
    private_ID = models.IntegerField(default=0)
    name = models.CharField(max_length=16, default="Nonam")
    generation = models.IntegerField(default=0)
    colony = models.ForeignKey(Colony, on_delete=models.CASCADE)
    is_alive = models.BooleanField(default=True)
    hp = models.IntegerField(default=5)
    max_hp = models.IntegerField(default=5)
    fertile = models.BooleanField(default=True)
    starving = models.BooleanField(default=False)
    #action = models.CharField(max_length=32, choices=TORB_ACTION_OPTIONS, default='gathering',)
    
    # Genes
    #vitality = models.JSONField(default=default_gene_alleles)
    #sturdiness = models.JSONField(default=default_gene_alleles)
    #agility = models.JSONField(default=default_gene_alleles)
    #strength = models.JSONField(default=default_gene_alleles)
    
    @property
    def status(self):
        if not self.is_alive:
            return "Dead"
        elif self.starving:
            return "Starving"
        else:
            return "Alive"