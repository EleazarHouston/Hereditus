import logging
import random

from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Now

from .game import Game
from .story_text import StoryText
from .torb_names import torb_names

logger = logging.getLogger('hereditus')

class Colony(models.Model):
    from .torb import Torb
    player = models.ForeignKey(User, on_delete=models.CASCADE, default=None, null=True, blank=True)
    name = models.CharField(max_length=64, default="DefaultName")
    game = models.ForeignKey('main_game.Game', on_delete=models.CASCADE, null=True)
    food = models.IntegerField(default=5)
    ready = models.BooleanField(default=False)
    rest_heal_flat = models.IntegerField(default=2)
    rest_heal_perc = models.FloatField(default=0.2)
    gather_rate = models.FloatField(default=1.7)
    discovered_colonies = models.ManyToManyField('self', symmetrical=False, related_name='discoverers', blank=True)
    army = models.OneToOneField('main_game.Army', on_delete=models.SET_NULL, null=True, blank=True, related_name='colony_army')
    
    @property
    def torb_count(self):
        return self.torb_set.count()
    
    
    @property
    def num_soldiers(self):
        return len([torb for torb in self.torb_set.all() if torb.action == "soldiering"])
    
    @property
    def num_training(self):
        return len([torb for torb in self.torb_set.all() if torb.action == "training" and torb.is_alive])
    
    def new_round(self, round_number: int):
        self.reset_fertility()
        self.gather_phase()
        self.grow_torbs()
        self.call_breed_torbs()
        self.rest_torbs()
        self.army.new_round()
        self.colony_meal()
        self.scout_target = None
        self.save()
        StoryText.objects.create(
            colony=self,
            story_text_type="system",
            story_text=f"It is now year {round_number}.",
            timestamp=Now())
                
    def reset_fertility(self):
        for torb in self.torb_set.filter(is_alive=True, growing=False):
            torb.fertile = True
            torb.save()
            
    def grow_torbs(self):
        growing_torbs = self.torb_set.filter(growing=True)
        for torb in growing_torbs:
            torb.growing = False
            torb.set_action("gathering", "🌾 Gathering")
            torb.save()
    
    def call_breed_torbs(self):
        checked_torbs = []
        for torb in self.torb_set.all():
            if torb.action == "breeding" and torb not in checked_torbs:
                checked_torbs.append(torb)
                checked_torbs.append(torb.context_torb)
                torb1 = torb.context_torb
                new_torb = self.game.evolution_engine_instance.breed_torbs(colony=self, torb0=torb, torb1=torb.context_torb)
                if new_torb:
                    StoryText.objects.create(
                        colony=self,
                        story_text_type="breeding",
                        story_text=f"A new Torb, '{new_torb.name}', was born",
                        timestamp=Now())
                torb.set_action("gathering", "🌾 Gathering")
                torb1.set_action("gathering", "🌾 Gathering")
        
    def set_breed_torbs(self, torbs):
        from .torb import Torb
        self.discovered_colonies.add(self)
        torb0 = Torb.objects.get(id=torbs[0])
        torb1 = Torb.objects.get(id=torbs[1])
        
        torb0.set_action("breeding", f"💦 Breeding with {torb1.name}", torb1)
        torb1.set_action("breeding", f"💦 Breeding with {torb0.name}", torb0)

    def rest_torbs(self):
        for torb in self.torb_set.all():
            if torb.action == "resting" and not torb.starving:
                adjust_amount = round(self.rest_heal_flat + self.rest_heal_perc & torb.max_hp)
                torb.adjust_hp(adjust_amount, context="resting")
    
    def reset_torbs_actions(self, action: str):
        for torb in self.torb_set.all():
            torb.set_action("gathering", "🌾 Gathering")
    
    def gather_phase(self):
        num_gathering = 0
        for torb in self.torb_set.all():
            if torb.action == "gathering":
                num_gathering += 1
        food_gathered = round(num_gathering * self.gather_rate)
        self.food += food_gathered
        self.save()
        StoryText.objects.create(
            colony=self,
            story_text_type="food",
            story_text=f"Your Torbs gathered {food_gathered} food.",
            timestamp=Now())
        
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
        StoryText.objects.create(
            colony=self,
            story_text_type="food",
            story_text=f"Your Torbs ate {less_food} food and {len(starved_torbs)} went hungry.",
            timestamp=Now())
            
    def ready_up(self):
        self.ready = True
        self.save()
        logger.info(f"Colony '{self.name}' readied up")
        self.game.check_ready_status()
    
    def new_torb(self, genes, generation):
        from .torb import Torb
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
        for _ in range(self.game.starting_torbs):
            self.game.evolution_engine_instance.protogenesis_torb(colony=self)

    def save(self, *args, **kwargs):
        from .army import Army
        army, created = Army.objects.get_or_create(colony=self)
        if created or not self.army:
            self.army = army
        
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"A new colony '{self.name}' was made")
            self.init_torbs()
            self.discovered_colonies.add(self)
            StoryText.objects.create(
                colony=self,
                story_text_type="system",
                story_text="Welcome to Hereditus!",
                timestamp=Now())
        from .army import Army
        army, created = Army.objects.get_or_create(colony=self)
        if created or not self.army:
            self.army = army
            self.save()
            
    def __str__(self):
        return self.name
    
    