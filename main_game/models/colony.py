import logging
import random

from django.contrib.auth.models import User
from django.db import models
from django.db.models.functions import Now

from .game import Game
from .story_text import StoryText
from .torb_names import torb_names
from .player import AIPlayer

logger = logging.getLogger('hereditus')

class Colony(models.Model):
    from .torb import Torb
    player = models.ForeignKey('Player', null=True, blank=True, default=None, on_delete=models.SET_NULL, related_name='colonies')
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
        return self.torbs.filter(is_alive=True).count()
    
    @property
    def num_soldiers(self):
        return len([torb for torb in self.torbs.all() if torb.action == "soldiering" and torb.is_alive])
    
    @property
    def num_training(self):
        return len([torb for torb in self.torbs.all() if torb.action == "training" and torb.is_alive])
    
    def new_round(self, round_number: int):
        self.reset_fertility()
        self.gather_phase()
        self.grow_torbs()
        self.call_breed_torbs()
        self.rest_torbs()
        self.army.new_round()
        self.colony_meal()
        #self.scout_target = None # Moved to army
        self.save()
        StoryText.objects.create(
            colony=self,
            story_text_type="system",
            story_text=f"It is now year {round_number+1}.",
            timestamp=Now())
                
    def reset_fertility(self):
        for torb in self.torbs.filter(is_alive=True, growing=False):
            torb.fertile = True
            torb.save()
            
    def grow_torbs(self):
        growing_torbs = self.torbs.filter(growing=True)
        for torb in growing_torbs:
            torb.growing = False
            torb.set_action(action="gathering")
            torb.save()
    
    def call_breed_torbs(self):
        checked_torbs = []
        for torb in self.torbs.all():
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
                torb.set_action(action="gathering")
                torb1.set_action(action="gathering")
        
    def set_breed_torbs(self, torbs):
        from .torb import Torb
        self.discovered_colonies.add(self)
        torb0 = Torb.objects.get(id=torbs[0])
        torb1 = Torb.objects.get(id=torbs[1])
        
        torb0.set_action(action="breeding", context_torb=torb1)
        torb1.set_action(action="breeding", context_torb=torb0)

    def assign_torbs_action(self, torb_ids, action):
        from .torb import Torb
        torbs = Torb.objects.filter(id__in=torb_ids, colony=self)
        for torb in torbs:
            torb.set_action(action=action)

    def rest_torbs(self):
        for torb in self.torbs.all():
            if torb.action == "resting" and not torb.starving:
                adjust_amount = round(self.rest_heal_flat + self.rest_heal_perc & torb.max_hp)
                torb.adjust_hp(adjust_amount, context="resting")
    
    def reset_torbs_actions(self, action: str):
        for torb in self.torbs.all():
            torb.set_action(action="gathering")
    
    def gather_phase(self):
        num_gathering = 0
        for torb in self.torbs.all():
            if torb.action == "gathering":
                num_gathering += 1
        food_gathered = round(num_gathering * self.gather_rate)
        self.adjust_food(food_gathered)
        StoryText.objects.create(
            colony=self,
            story_text_type="food",
            story_text=f"Your Torbs gathered {food_gathered} food.",
            timestamp=Now())
    
    def adjust_food(self, adjust_amount):
        adjust_amount = int(adjust_amount)
        self.food = max(self.food + adjust_amount, 0)
        self.save()
    
    def colony_meal(self):
        living_torbs = [torb for torb in self.torbs.all() if torb.is_alive]
        starved_torbs = []
        
        if self.food < len(living_torbs):
            starved_torbs = random.sample(living_torbs, len(living_torbs) - self.food)
            for torb in starved_torbs:
                torb.starving = True
                torb.adjust_hp(-1, context="starvation")
        less_food = 0
        for torb in living_torbs:
            if torb not in starved_torbs:
                food_meal_amount = 1
                torb.starving = False
                torb.adjust_hp(1, context="eating a good meal")
                torb.save()
                less_food += food_meal_amount
        self.adjust_food(-1 * less_food)
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
        next_ID = Torb.objects.filter(colony=self).aggregate(max_id=models.Max('private_ID'))['max_id']
        next_ID = next_ID + 1 if next_ID is not None else 1
        
        used_names = set(Torb.objects.filter(colony=self).values_list('name', flat=True))
        available_names = [name for name in torb_names if name not in used_names]
        
        if available_names:
            name = random.choice(available_names)
        else:
            base_name = random.choice(torb_names)
            counter = 2
            name = base_name
            while name in used_names:
                name = f"{base_name} {counter}"
                counter += 1
        
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
        
        if is_new and isinstance(self.player, AIPlayer):
            self.player.make_decisions(self)
            
    def __str__(self):
        return self.name