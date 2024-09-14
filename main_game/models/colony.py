from django.db import models
from django.contrib.auth.models import User
import logging
import random
from .game import Game

from .story_text import StoryText
from django.db.models.functions import Now

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
    
    # TODO: Implement
    scout_target = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='scouting_colonies')
    attack_target= models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='attacking_colonies')
    
    @property
    def torb_count(self):
        return self.torb_set.count()
    
    @property
    def num_soldiers(self):
        return len([torb for torb in self.torb_set.all() if torb.action == "soldiering"])
    
    @property
    def num_training(self):
        return len([torb for torb in self.torb_set.all() if torb.action == "training"])
    
    @property
    def army_health(self):
        return sum([torb.hp for torb in self.torb_set.all() if torb.action == "soldiering"])
    
    @property
    def army_power(self):
        return sum([torb.power for torb in self.torb_set.all() if torb.action == "soldiering"])
    
    @property
    def army_resilience(self):
        return sum([torb.resilience for torb in self.torb_set.all() if torb.action == "soldiering"])
    
    def new_round(self, round_number: int):
        self.reset_fertility()
        self.grow_torbs()
        self.call_breed_torbs()
        self.rest_torbs()
        self.train_soldiers()
        self.gather_phase()
        self.scout_colony()
        self.colony_meal()
        
        #self.reset_torbs_actions("gathering")
        StoryText.objects.create(colony=self, story_text_type="system", story_text=f"It is now year {round_number}.", timestamp=Now())
                
    def reset_fertility(self):
        for torb in self.torb_set.all():
            torb.fertile = True
            torb.save()
            
    def grow_torbs(self):
        for torb in self.torb_set.all():
            torb.growing = False
            torb.save()
    
    def scout_colony(self):
        colony_to_scout = self.scout_target
        if not colony_to_scout:
            return False
        if self.num_soldiers == 0:
            StoryText.objects.create(colony=self, story_text_type="system", story_text=f"You ordered your Torbs to scout, but without training all they found was {self.name}.", timestamp=Now())
            return False
        if colony_to_scout.num_soldiers == 0:
            self.discovered_colonies.add(colony_to_scout)
            StoryText.objects.create(colony=self, story_text_type="system", story_text=f"Your scout found {colony_to_scout.name} and they reported that it appears undefended.", timestamp=Now())
            return True
        random_enemy_torb_power = random.choice([torb.power for torb in colony_to_scout.torb_set.all() if torb.action == "soldiering"])
        random_ally_soldier = random.choice([torb for torb in self.torb_set.all() if torb.action == "soldiering"])
        random_ally_torb_resilience = random_ally_soldier.resilience
        if random_ally_torb_resilience > random_enemy_torb_power:
            self.discovered_colonies.add(colony_to_scout)
            StoryText.objects.create(colony=self, story_text_type="system", story_text=f"An enemy soldier at {colony_to_scout.name} tried to repell your scout, but {random_ally_soldier.name} was too nimble.", timestamp=Now())
            return True
        if random.uniform(0, 1) > (random_enemy_torb_power / random_ally_torb_resilience):
            self.discovered_colonies.add(colony_to_scout)
            StoryText.objects.create(colony=self, story_text_type="system", story_text=f"Your scout was lucky and wasn't caught by a soldier at {colony_to_scout.name}.", timestamp=Now())
            return True
        damage_to_take = random.randint(0, round(random_enemy_torb_power - random_ally_torb_resilience,0))
        if colony_to_scout in self.discovered_colonies:
            StoryText.objects.create(colony=self, story_text_type="system", story_text=f"Your scout was attacked when trying to scout {colony_to_scout.name} and didn't get any new information.", timestamp=Now())
        else:
            StoryText.objects.create(colony=self, story_text_type="system", story_text=f"Your scout was attacked when trying to scout an unknown colony and didn't get any information.", timestamp=Now())
        random_ally_soldier.adjust_hp(-1 * damage_to_take)
        self.scout_target = None
        self.save()
        return False
        
    def call_breed_torbs(self):
        
        checked_torbs = []
        for torb in self.torb_set.all():
            if torb.action == "breeding" and torb not in checked_torbs:
                checked_torbs.append(torb)
                checked_torbs.append(torb.context_torb)
                torb1 = torb.context_torb
                new_torb = self.game.evolution_engine.breed_torbs(colony=self, torb0=torb, torb1=torb.context_torb)
                if new_torb:
                    StoryText.objects.create(colony=self, story_text_type="breeding", story_text=f"A new Torb, '{new_torb.name}', was born", timestamp=Now())
                torb.set_action("gathering", "Gathering")
                torb1.set_action("gathering", "Gathering")
        
    def set_breed_torbs(self, torbs):
        from .torb import Torb
        self.discovered_colonies.add(self)
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