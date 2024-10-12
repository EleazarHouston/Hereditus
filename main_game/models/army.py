import logging
import random

from django.db import models
from django.db.models.functions import Now

from .story_text import StoryText

logger = logging.getLogger('hereditus')

class Army(models.Model):
    from .torb import Torb
    colony = models.OneToOneField('main_game.Colony', on_delete=models.CASCADE, related_name='army_instance')
    scout_target = models.ForeignKey('colony', blank=True, null=True, on_delete=models.SET_NULL, related_name='scouting_armies')
    attack_target= models.ForeignKey('colony', blank=True, null=True, on_delete=models.SET_NULL, related_name='attacking_armies')
    
    @property
    def army_health(self):
        return sum(army_torb.torb.hp for army_torb in self.army_torbs.all())
    
    @property
    def army_power(self):
        return sum(army_torb.power for army_torb in self.army_torbs.all())
    
    @property
    def army_resilience(self):
        return sum(army_torb.resilience for army_torb in self.army_torbs.all())
    
    def __str__(self):
        return f"Army of {self.colony.name}"
    
    def new_round(self):
        self.train_soldiers()
        self.scout_colony()
        self.purge_soldiers()

    def train_soldiers(self):
        for torb in self.colony.torb_set.all():
            if torb.action == "training":
                torb.trained = True
                torb.set_action("soldiering", "🏹 Soldiering")
                torb.save()
                ArmyTorb.add_to_army(self, torb)
                
    def purge_soldiers(self):
        for torb in self.colony.torb_set.all():
            if torb.action != "soldiering":
                self.remove_torb_from_army(torb)
    
    def remove_torb_from_army(self, torb):
        army_torb = ArmyTorb.objects.filter(army=self, torb=torb).first()
        if army_torb:
            army_torb.remove_from_army()
            
    def set_scout_target(self, scout_target):
        from .colony import Colony
        scout_target_colony = Colony.objects.get(id=scout_target)
        logger.debug(f"{self.colony.name}: Set scout_target as {scout_target_colony.name}")
        if scout_target_colony == self.colony:
            StoryText.objects.create(
                colony=self.colony,
                story_text_type="system",
                story_text=f"We likely won't get any new information trying to scout ourselves.",
                timestamp=Now())
            return
        
        if self.scout_target and self.scout_target in self.colony.discovered_colonies.all():
            StoryText.objects.create(colony=self.colony,
                                     story_text_type="system",
                                     story_text=f"Our new scout target is {scout_target_colony.name}.",
                                     timestamp=Now())
        elif self.scout_target in self.colony.discovered_colonies.all():
            StoryText.objects.create(colony=self,
                                     story_text_type="system",
                                     story_text=f"Our scout target is {scout_target_colony.name}.",
                                     timestamp=Now())
        else:
            StoryText.objects.create(colony=self.colony,
                                     story_text_type="system",
                                     story_text=f"Our scouts will go out and learn about the as-yet-unknown colony.",
                                     timestamp=Now())
        self.scout_target = scout_target_colony
        self.save()
    
    def scout_colony(self):
        colony_to_scout = self.scout_target
        if not colony_to_scout:
            logger.debug(f"{self.colony.name}: No target colony to scout")
            return False
        
        if self.colony.num_soldiers == 0:
            self._scout_no_soldiers()
            return False

        if colony_to_scout.num_soldiers == 0:
            self._scout_undefended_colony(colony_to_scout)
            return True
        
        random_enemy_torb_power = self._scout_random_enemy_power(colony_to_scout)
        random_ally_soldier = random.choice([soldier for soldier in self.army_torbs.all()])
        random_ally_torb_resilience = random_ally_soldier.resilience

        if random_ally_torb_resilience > random_enemy_torb_power:
            self._scout_successful(random_ally_soldier, colony_to_scout)
            return True

        if random.uniform(0, 1) > (random_enemy_torb_power / random_ally_torb_resilience):
            self._scout_lucky_escape(colony_to_scout)
            return True
        
        self._scout_failed(random_ally_soldier, colony_to_scout, random_enemy_torb_power, random_ally_torb_resilience)
        self.scout_target = None
        self.save()
        return False

    # Helper scout methods
    def _scout_no_soldiers(self):
        StoryText.objects.create(
            colony=self.colony,
            story_text_type="scout",
            story_text=f"You ordered your Torbs to scout, but without training all they found was {self.colony.name}.",
            timestamp=Now(),
        )

    def _scout_undefended_colony(self, colony_to_scout):
        self.colony.discovered_colonies.add(colony_to_scout)
        self.colony.save()
        StoryText.objects.create(
            colony=self.colony,
            story_text_type="scout",
            story_text=f"Your scout found {colony_to_scout.name} and they reported that it appears undefended.",
            timestamp=Now(),
        )

    def _scout_random_enemy_power(self, colony_to_scout):
        return random.choice([soldier.power for soldier in colony_to_scout.army.army_torbs.all()])

    def _scout_successful(self, random_ally_soldier, colony_to_scout):
        self.colony.discovered_colonies.add(colony_to_scout)
        self.colony.save()
        StoryText.objects.create(
            colony=self.colony,
            story_text_type="scout",
            story_text=f"An enemy soldier at {colony_to_scout.name} tried to repell your scout, but {random_ally_soldier.torb.name} was too nimble.",
            timestamp=Now(),
        )
        StoryText.objects.create(
            colony=colony_to_scout,
            story_text_type="enemy",
            story_text=f"Your soldiers tried to neutralize a scout from {self.colony.name}, but they were too quick and got away.",
            timestamp=Now(),
        )

    def _scout_lucky_escape(self, colony_to_scout):
        self.colony.discovered_colonies.add(colony_to_scout)
        self.colony.save()
        StoryText.objects.create(
            colony=self.colony,
            story_text_type="scout",
            story_text=f"Your scout was lucky and wasn't caught by a soldier at {colony_to_scout.name}.",
            timestamp=Now(),
        )
        StoryText.objects.create(
            colony=colony_to_scout,
            story_text_type="enemy",
            story_text=f"An enemy soldier was seen scouting your colony and was too quick to be identified.",
            timestamp=Now(),
        )

    def _scout_failed(self, random_ally_soldier, colony_to_scout, random_enemy_torb_power, random_ally_torb_resilience):
        damage_to_take = random.randint(0, round(random_enemy_torb_power - random_ally_torb_resilience, 0))
        if colony_to_scout in self.colony.discovered_colonies.all():
            story_text = f"Your scout was attacked when trying to scout {colony_to_scout.name} and didn't get any new information."
        else:
            story_text = "Your scout was attacked when trying to scout an unknown colony and didn't get any information."
        StoryText.objects.create(
            colony=self.colony,
            story_text_type="scout",
            story_text=story_text,
            timestamp=Now(),
        )
        random_ally_soldier.torb.adjust_hp(-1 * damage_to_take, context="an enemy soldier while scouting")
        if not random_ally_soldier.torb.is_alive:
            StoryText.objects.create(
                colony=colony_to_scout,
                story_text_type="enemy",
                story_text=f"Your soldiers fended off and killed a scout from {self.colony.name}.",
                timestamp=Now(),
            )
        else:
            StoryText.objects.create(
                colony=colony_to_scout,
                story_text_type="enemy",
                story_text=f"Your soldiers damaged an enemy scout from {self.colony.name}, but weren't able to finish the job.",
                timestamp=Now(),
            )
            
    
    

# Keep ArmyTorb in same file as Army
class ArmyTorb(models.Model):
    army = models.ForeignKey('main_game.Army', on_delete=models.CASCADE, related_name='army_torbs')
    torb = models.ForeignKey('main_game.Torb', on_delete=models.CASCADE)
    active_alleles = models.JSONField(default=dict)
    
    @property
    def power(self):
        return round((self.active_alleles['strength'] * self.active_alleles['agility'])**0.5, 2)
    
    @property
    def resilience(self):
        return round((self.active_alleles['vitality'] * self.active_alleles['sturdiness'])**0.5, 2)
    
    @classmethod
    def add_to_army(cls, army, torb):
        # Randomly select alleles for power and resilience when adding the Torb to the army
        strength_allele = random.choice(torb.genes['strength'])
        agility_allele = random.choice(torb.genes['agility'])
        vitality_allele = random.choice(torb.genes['vitality'])
        sturdiness_allele = random.choice(torb.genes['sturdiness'])

        return cls.objects.create(
            army=army,
            torb=torb,
            active_alleles = {
                'strength': strength_allele,
                'agility': agility_allele,
                'vitality': vitality_allele,
                'sturdiness': sturdiness_allele
            }
        )

    def remove_from_army(self):
        self.delete()