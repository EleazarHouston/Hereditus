from django.db import models
from django.db.models.signals import post_save, post_delete
from django.db.models.functions import Now
from django.dispatch import receiver
from .torb_names import torb_names
import random
import numpy as np
import logging
import time

logger = logging.getLogger('hereditus')

class Game(models.Model):
    starting_torbs = models.IntegerField(default=4)
    description = models.CharField(max_length=256, null=True)
    evolution_engine = models.OneToOneField('EvolutionEngine', on_delete=models.SET_NULL, null=True, blank=True, related_name='game_instance')
    round_number = models.IntegerField(default=1)
    
    def __str__(self):
        return self.description
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"A new Game '{self.description}' was made.")
    
    def next_round(self):
        
        # have whatever calls this by default check if all colonies are ready
        # do combat here
        
        for colony in self.colony_set.all():
            colony.new_round(round_number = self.round_number)
            
        # Done in a separate loop because web GUIs are updated when ready value is updated
        for colony in self.colony_set.all():
            colony.ready = False
            colony.save()
        self.round_number += 1
        self.save()
        logger.debug(f"Next round processed successfully")
    
    def check_ready_status(self):
        for colony in self.colony_set.all():
            if not colony.ready:
                return False
        logger.debug(f"All colonies are ready for the next round")
        self.next_round()
    
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
    gene_list =         models.JSONField(default=default_gene_list)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"A new EvolutionEngine '{self.pk}' was made for Game {self.game}")
    
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
        torb = self.new_torb(generation=0, colony=colony, genes=genes)
        
    def __str__(self):
        return f"EvolutionEngine{self.pk} for Game '{self.game.description}'"
    
    def breed_torbs(self, colony, torb0, torb1):
        if not self.check_torb_breedable(torb0) or not self.check_torb_breedable(torb1):
            logger.debug(f"An EvolutionEngine for Colony {colony} in {self.game} tried to breed Torb {torb0.private_ID} '{torb0.name}' and Torb {torb1.private_ID} '{torb1.name}' but one/both weren't breedable")
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
        logger.debug(f"An EvolutionEngine for Colony {colony} in {self.game} is breeding Torb {torb0.private_ID} '{torb0.name}' and Torb {torb1.private_ID} '{torb1.name}'")
        baby_torb = self.new_torb(generation=generation, colony=colony, genes=genes)
        baby_torb.growing = True
        
        torb0.fertile = torb1.fertile = baby_torb.fertile = False
        torb0.save()
        torb1.save()
        baby_torb.set_action("growing", "Growing")
        baby_torb.save()
        
        return baby_torb
    
    def mutate_and_shuffle(self, alleles):
        out_alleles = []
        for allele in alleles:
            die_roll = random.uniform(0, 1)
            if die_roll >= 1 - self.mutation_chance:
                allele_hist = allele # To be used in logging: allele mutated from hist to X
                mutation_amount = np.random.normal(0, self.mutation_dev)
                allele = round(allele * (1 + mutation_amount), 4)
            out_alleles.append(allele)
        random.shuffle(out_alleles)
        return out_alleles
                
                    
    def new_torb(self, generation, colony, genes):
        torb = colony.new_torb(generation=generation, genes=genes)
        logger.debug(f"An EvolutionEngine for Colony {colony} in {self.game} created new Torb {torb.private_ID} '{torb.name}' with Genes {genes}")
        return torb
        

class Colony(models.Model):
    name = models.CharField(max_length=64, default="DefaultName")
    game = models.ForeignKey(Game, on_delete=models.CASCADE, null=True)
    food = models.IntegerField(default=5)
    ready = models.BooleanField(default=False)
    rest_heal_flat = models.IntegerField(default=2)
    rest_heal_perc = models.FloatField(default=0.2)
    gather_rate = models.FloatField(default=1.7)
    discovered_colonies = models.ManyToManyField('self', symmetrical=False, related_name='discoverers', blank=True)
    
    @property
    def torb_count(self):
        return self.torb_set.count()
    
    def new_round(self, round_number: int):
        self.reset_fertility()
        self.grow_torbs()
        self.call_breed_torbs()
        self.rest_torbs()
        self.train_soldiers()
        self.gather_phase()
        self.colony_meal()
        self.reset_torbs_actions("gathering")
        StoryText.objects.create(colony=self, story_text_type="system", story_text=f"It is now year {round_number}.", timestamp=Now())
                
    def reset_fertility(self):
        for torb in self.torb_set.all():
            torb.fertile = True
            torb.save()
            
    def grow_torbs(self):
        for torb in self.torb_set.all():
            torb.growing = False
            torb.save()
    
    def call_breed_torbs(self):
        
        checked_torbs = []
        for torb in self.torb_set.all():
            if torb.action == "breeding" and torb not in checked_torbs:
                checked_torbs.append(torb)
                checked_torbs.append(torb.context_torb)
                new_torb = self.game.evolution_engine.breed_torbs(colony=self, torb0=torb, torb1=torb.context_torb)
                if new_torb:
                    StoryText.objects.create(colony=self, story_text_type="breeding", story_text=f"A new Torb, '{new_torb.name}', was born", timestamp=Now())
        
    def set_breed_torbs(self, torbs):
        self.discovered_colonies.add(self)
        print(self.discovered_colonies.all())
        logger.debug(f"{self.name}'s discovered colonies: {self.discovered_colonies.all()}")
        torb0 = Torb.objects.get(id=torbs[0])
        torb1 = Torb.objects.get(id=torbs[1])
        
        torb0.set_action("breeding", f"Breeding with {torb1.name}", torb1)
        torb1.set_action("breeding", f"Breeding with {torb0.name}", torb0)

    def rest_torbs(self):
        for torb in self.torb_set.all():
            if torb.action == "resting" and not torb.starving:
                adjust_amount = round(self.rest_heal_flat + self.rest_heal_perc & torb.max_hp)
                torb.adjust_hp(adjust_amount, context="resting")
    
    def reset_torbs_actions(self, action: str):
        for torb in self.torb_set.all():
            torb.set_action("gathering", "Gathering")
    
    def gather_phase(self):
        num_gathering = 0
        for torb in self.torb_set.all():
            if torb.action == "gathering":
                num_gathering += 1
        food_gathered = round(num_gathering * self.gather_rate)
        self.food += food_gathered
        self.save()
        StoryText.objects.create(colony=self, story_text_type="food", story_text=f"Your Torbs gathered {food_gathered} food.", timestamp=Now())
        
    def train_soldiers(self):
        for torb in self.torb_set.all():
            if torb.action == "training":
                torb.trained = True
                torb.set_action("soldiering", "Soldiering")
                torb.save()
        
    def colony_meal(self):
        living_torbs = [torb for torb in self.torb_set.all() if torb.is_alive]
        starved_torbs = []
        
        if self.food < len(living_torbs):
            starved_torbs = random.sample(living_torbs, len(living_torbs) - self.food)
            for torb in starved_torbs:
                torb.starving = True
                torb.adjust_hp(-1, context="starvation")
        less_food = 0
        for torb in living_torbs:
            if torb not in starved_torbs:
                adjust_amount = 1
                torb.starving = False
                torb.adjust_hp(1)
                torb.save()
                less_food += 1
        
        self.food = max(self.food - less_food, 0)
        self.save()
        StoryText.objects.create(colony=self, story_text_type="food", story_text=f"Your Torbs ate {less_food} food and {len(starved_torbs)} went hungry.", timestamp=Now())
            
    def ready_up(self):
        self.ready = True
        self.save()
        logger.info(f"Colony '{self.name}' readied up")
        self.game.check_ready_status()
        logger.debug(f"{self.name}'s discovered colonies: {self.discovered_colonies.all()}")
    
    def new_torb(self, genes, generation):
        next_ID = self.torb_count + 1
        random.shuffle(torb_names)
        name = torb_names[0]
        max_hp = genes['vitality'][0]
        torb = Torb.objects.create(
            colony=self,
            private_ID=next_ID,
            name=name,
            genes=genes,
            generation=generation,
            max_hp=max_hp,
            hp=max_hp)
        return torb
        
    def init_torbs(self):
        for i in range(self.game.starting_torbs):
            self.game.evolution_engine.protogenesis_torb(colony=self)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"A new colony '{self.name}' was made")
            self.init_torbs()
            self.discovered_colonies.add(self)
            logger.debug(f"{self.name}'s discovered colonies: {self.discovered_colonies.all()}")
            StoryText.objects.create(colony=self, story_text_type="system", story_text="Welcome to Hereditus!", timestamp=Now())

    def __str__(self):
        return self.name
        
class StoryText(models.Model):
    colony = models.ForeignKey(Colony, on_delete=models.CASCADE)
    story_text_type = models.CharField(max_length=32, default="default")
    story_text = models.CharField(max_length=1028, default="N/A")
    timestamp = models.DateTimeField()

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
    colony = models.ForeignKey(Colony, on_delete=models.CASCADE)
    is_alive = models.BooleanField(default=True)
    hp = models.IntegerField(default=5)
    max_hp = models.IntegerField(default=5)
    fertile = models.BooleanField(default=True)
    starving = models.BooleanField(default=False)
    action = models.CharField(max_length=32, choices=TORB_ACTION_OPTIONS, default='gathering',)
    action_desc = models.CharField(max_length=256, default='Gathering')
    context_torb = models.ForeignKey("Torb", null=True, blank=True, on_delete=models.SET_NULL)
    growing = models.BooleanField(default=False)
    trained = models.BooleanField(default=False)
    
    
    # Genes
    genes = models.JSONField(default=dict)

    
    def __str__(self):
        return f"Colony {self.colony} Torb: {self.private_ID} '{self.name}'"
    
    def adjust_hp(self, adjust_amount, context="an unknown source"):
        self.hp = min(max(0, self.hp + adjust_amount), self.max_hp)
        if self.hp == 0:
            self.is_alive = False
            self.fertile = False
            StoryText.objects.create(colony=self, story_text_type="death", story_text=f"'{self.name}' (Torb {self.private_ID}) died from {context}.", timestamp=Now())
            logger.debug(f"Colony {self.colony.pid} '{self.colony.name}' Torb {self.private_ID} '{self.name}' died, context: {context}")
        self.save()
        
    def set_action(self, action: str, action_desc: str, context_torb=None):
        if self.growing:
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
        
        return out_text
        