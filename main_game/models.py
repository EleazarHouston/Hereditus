from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .torb_names import torb_names
import random
import numpy as np

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
    return ["vitality", "sturdiness", "agility", "strength"]

def default_gene_alleles():
    return [5, 5]

class EvolutionEngine(models.Model):
    game = models.OneToOneField(Game, on_delete=models.CASCADE, related_name='evolution_engine_instance')
    random_gene_min =   models.IntegerField(default=1)
    random_gene_max =   models.IntegerField(default=10)
    mutation_chance =   models.FloatField(default=0.1)
    mutation_dev =      models.FloatField(default=0.15)
    alleles_per_gene =  models.IntegerField(default=2)
    gene_list =         models.JSONField(default=default_gene_alleles)
    
    def check_torb_breedable(self, torb):
        if not torb.fertile:
            return False
        return True
    
    def protogenesis_torb(self, colony):
        genes = {}
        for gene in self.gene_list:
            alleles = []
            for i in range(self.alleles_per_gene):
                alleles.append(random.randrange(self.random_gene_min, self.random_gene_max))
            genes[gene] = alleles
        self.new_torb(generation=0, colony=colony, genes=genes)
        
    
    def breed_torbs(self, colony, torb0, torb1):
        if not self.check_torb_breedable(torb1) or not self.check_torb_breedable(torb1):
            return False
        genes = {}
        generation = max(torb0.generation, torb1.generation) + 1
        for gene in self.gene_list:
            alleles = []
            p0_gene = torb0.genes[gene]
            p1_gene = torb1.genes[gene]
            random.shuffle(p0_gene)
            random.shuffle(p1_gene)
            num_alleles = min(len(p0_gene), len(p1_gene))
            
            for i in range(num_alleles):
                # The first allele is a randomly chosen one from the parents
                # subsequent alleles are avg of random alleles from each parent, non-replacing
                if i == 0:
                    alleles.append(random.choice([p0_gene[i], p1_gene[i]]))
                else:
                    alleles.append(round(np.mean([p0_gene[i], p1_gene[i]]),4))
            alleles = self.mutate_and_shuffle(alleles)
            genes[gene] = alleles
        print("1")
        print(genes)
        self.new_torb(generation=generation, colony=colony, genes=genes)
        torb0.fertile = torb1.fertile = False
        torb0.action = torb1.action = 'breeding'
        torb0.action_desc = f"Breeding with {torb1.name}"
        torb1.action_desc = f"Breeding with {torb0.name}"
        torb0.save()
        torb1.save()
    
    def mutate_and_shuffle(self, alleles):
        out_alleles = []
        for allele in alleles:
            die_roll = random.uniform(0, 1)
            if die_roll > 1 - self.mutation_chance:
                allele_hist = allele # To be used in logging: allele mutated from hist to X
                mutation_amount = np.random.normal(0, self.mutation_dev)
                allele = round(allele * (1 + mutation_amount), 4)
            out_alleles.append(allele)
        random.shuffle(out_alleles)
        return out_alleles
                
                    
    def new_torb(self, generation, colony, genes):
        print(genes)
        colony.new_torb(generation=generation, genes=genes)
        

class Colony(models.Model):
    name = models.CharField(max_length=64, default="DefaultName")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True)
    food = models.IntegerField(default=5)
    ready = models.BooleanField(default=False)
    
    @property
    def torb_count(self):
        return self.torb_set.count()
    
    def new_torb(self, genes, generation):
        next_ID = self.torb_count + 1
        random.shuffle(torb_names)
        name = torb_names[0]
        max_hp = genes['vitality'][0]
        Torb.objects.create(
            colony=self,
            private_ID=next_ID,
            name=name,
            genes=genes,
            generation=generation,
            max_hp=max_hp,
            hp=max_hp)
        
    def init_torbs(self):
        for i in range(self.game.starting_torbs):
            self.game.evolution_engine.protogenesis_torb(colony=self)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.init_torbs()
    
    def __str__(self):
        return self.name
        


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
    action = models.CharField(max_length=32, choices=TORB_ACTION_OPTIONS, default='gathering',)
    action_desc = models.CharField(max_length=256, default='Gathering')
    
    # Genes
    genes = models.JSONField(default=dict)
    vitality = models.JSONField(default=list)
    sturdiness = models.JSONField(default=list)
    agility = models.JSONField(default=list)
    strength = models.JSONField(default=list)
    
    @property
    def status(self):
        if not self.is_alive:
            return "Dead"
        elif self.starving:
            return "Starving"
        else:
            return "Alive"