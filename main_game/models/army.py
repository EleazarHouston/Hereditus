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
    morale = models.IntegerField(default=100)
    
    @property
    def army_health(self):
        return round(sum(army_torb.torb.hp for army_torb in self.army_torbs.all()),0)
    
    @property
    def army_power(self):
        return round(sum(army_torb.power for army_torb in self.army_torbs.all()),2)
    
    @property
    def army_resilience(self):
        return round(sum(army_torb.resilience for army_torb in self.army_torbs.all()),2)
    
    def __str__(self):
        return f"Army of {self.colony.name}"
    
    def new_round(self):
        self.purge_soldiers()
        self.scout_colony()
        self.attack_colony()
        self.train_soldiers()
        self.scout_target = None
        self.attack_target = None
        self.save()

    def train_soldiers(self):
        for torb in self.colony.torbs.all():
            if torb.action == "training":
                torb.trained = True
                torb.set_action(action="soldiering",)
                torb.save()
                ArmyTorb.add_to_army(self, torb)
                
    def purge_soldiers(self):
        for torb in self.colony.torbs.all():
            if torb.action != "soldiering":
                self.remove_torb_from_army(torb)
    
    def remove_torb_from_army(self, torb):
        army_torb = ArmyTorb.objects.filter(army=self, torb=torb).first()
        if army_torb:
            army_torb.remove_from_army()
            
    def set_scout_target(self, scout_target_id):
        from .colony import Colony
        if not scout_target_id:
            self.scout_target = None
            self.save()
            StoryText.objects.create(
                colony=self.colony,
                story_text_type="scout",
                story_text=f"Our scouting plans have been canceled.",
                timestamp=Now())
            return
        
        scout_target_colony = Colony.objects.get(id=scout_target_id)
        logger.debug(f"{self.colony.name}: Set scout_target as {scout_target_colony}")
        if scout_target_colony == self.colony:
            StoryText.objects.create(
                colony=self.colony,
                story_text_type="scout",
                story_text=f"We likely won't get any new information trying to scout ourselves.",
                timestamp=Now())
            return
        
        if self.scout_target and self.scout_target in self.colony.discovered_colonies.all():
            StoryText.objects.create(colony=self.colony,
                                     story_text_type="scout",
                                     story_text=f"Our new scout target is {scout_target_colony.name}.",
                                     timestamp=Now())
        elif self.scout_target in self.colony.discovered_colonies.all():
            StoryText.objects.create(colony=self,
                                     story_text_type="scout",
                                     story_text=f"Our scout target is {scout_target_colony.name}.",
                                     timestamp=Now())
        else:
            StoryText.objects.create(colony=self.colony,
                                     story_text_type="scout",
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
            StoryText.objects.create(
                colony=self.colony,
                story_text_type="scout",
                story_text=f"You ordered your Torbs to scout, but without training all they found was {self.colony.name}.",
                timestamp=Now(),
                )
            return False

        if colony_to_scout.num_soldiers == 0:
            self._scout_undefended_colony(colony_to_scout)
            return True
        
        random_enemy_torb_power = random.choice([soldier.power for soldier in colony_to_scout.army.army_torbs.all()])
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
    
    # DRY, definitely a better way to do this, repeats a lot of set_scout_target
    def set_attack_target(self, attack_target_id):
        from .colony import Colony
        if not attack_target_id:
            self.attack_target = None
            self.save()
            StoryText.objects.create(
                colony=self.colony,
                story_text_type="combat",
                story_text=f"Our attack plans have been canceled.",
                timestamp=Now())
            return
        attack_target_colony = Colony.objects.get(id=attack_target_id)
        logger.debug(f"{self.colony.name}: Set attack_target as {attack_target_colony}")
        if attack_target_colony == self.colony:
            StoryText.objects.create(
                colony=self.colony,
                story_text_type="combat",
                story_text=f"Our soldiers will never agree to attack their own colony!",
                timestamp=Now())
            return
        if attack_target_colony not in self.colony.discovered_colonies.all():
            StoryText.objects.create(
                colony=self.colony,
                story_text_type="combat",
                story_text=f"We can't send our soldiers out without knowing where they're going!",
                timestamp=Now())
            return
        
        if self.attack_target:
            StoryText.objects.create(colony=self.colony,
                                     story_text_type="system",
                                     story_text=f"Our new attack target is {attack_target_colony.name}.",
                                     timestamp=Now())
        else:
            StoryText.objects.create(colony=self.colony,
                                     story_text_type="system",
                                     story_text=f"Our attack target is {attack_target_colony.name}.",
                                     timestamp=Now())
        self.attack_target = attack_target_colony
        self.save()
        
    def attack_colony(self):
        colony_to_attack = self.attack_target
        if not colony_to_attack:
            logger.debug(f"{self.colony}: No target colony to attack")
            return False
        logger.debug(f"{self.colony} is waging war against {colony_to_attack}")
        if self.colony.num_soldiers == 0:
            StoryText.objects.create(
                colony=self.colony,
                story_text_type="combat",
                story_text=f"You ordered your Torbs to attack, but without training they just bumbled about.",
                timestamp=Now(),
                )
            return False

        won_fight = None
        if colony_to_attack.num_soldiers == 0:
            won_fight = True
            StoryText.objects.create(
                colony=self.colony,
                story_text_type="combat",
                story_text=f"There was no army to defend your attack on {colony_to_attack.name}",
                timestamp=Now(),
                )
        else:
            won_fight = self.battle_army(enemy_army=colony_to_attack.army)
        if won_fight:
            self._attack_successful(colony_to_attack)
        else:
            self._attack_failed(colony_to_attack)
        self.attack_target = None
        self.save()
        
    def battle_army(self, enemy_army) -> bool:
        ally_enough_morale = True
        ally_enough_morale = self.morale > random.randrange(1, 50)
        while self.colony.num_soldiers > 0 and enemy_army.colony.num_soldiers > 0 and ally_enough_morale:
            ally_army_torb = self.army_torbs.all().order_by('?').first()
            enemy_army_torb = enemy_army.army_torbs.all().order_by('?').first()
            
            self.torb_fight(ally_army_torb, enemy_army_torb)
        
        if enemy_army.colony.num_soldiers == 0:
            return True
        else:
            return False
    
    def torb_fight(self, ally_army_torb, enemy_army_torb):
        logger.debug(f"{self.colony.name}: Torb {ally_army_torb} is fighting {enemy_army_torb.torb.colony}'s {enemy_army_torb}")
        ally_army_torb_attack   = random.uniform(1, ally_army_torb.power)
        ally_army_torb_defense  = random.uniform(1, ally_army_torb.resilience)
        
        enemy_army_torb_attack  = random.uniform(1, enemy_army_torb.power)
        enemy_army_torb_defense = random.uniform(1, enemy_army_torb.resilience)
        
        ally_army_torb_speed    = random.uniform(1, ally_army_torb.active_alleles['agility'])
        enemy_army_torb_speed   = random.uniform(1, enemy_army_torb.active_alleles['agility'])
        logger.debug(f"{self.colony.name}: Torb {ally_army_torb} has speed: {ally_army_torb_speed}, attack: {ally_army_torb_attack} and defense: {ally_army_torb_defense}")
        logger.debug(f"{enemy_army_torb.torb.colony}: Torb {enemy_army_torb} has speed: {enemy_army_torb_speed}, attack: {enemy_army_torb_attack} and defense: {enemy_army_torb_defense}")
        
        ally_hp_adjust = 0
        enemy_hp_adjust = 0
        
        if ally_army_torb_speed > enemy_army_torb_speed:
            enemy_hp_adjust = round(min(0, enemy_army_torb_defense - ally_army_torb_attack),0)
            enemy_army_torb.torb.adjust_hp(enemy_hp_adjust, context=f"defending against {self.colony.name}'s Army")
            if enemy_army_torb.torb.is_alive:
                ally_hp_adjust = round(min(0, ally_army_torb_defense - enemy_army_torb_attack),0)
                ally_army_torb.torb.adjust_hp(ally_hp_adjust, context=f"in a battle against {enemy_army_torb.torb.colony.name}")
        else: # Violates DRY
            ally_hp_adjust = round(min(0, ally_army_torb_defense - enemy_army_torb_attack),0)
            ally_army_torb.torb.adjust_hp(ally_hp_adjust, context=f"in a battle against {enemy_army_torb.torb.colony.name}")
            if enemy_army_torb.torb.is_alive:
                enemy_hp_adjust = round(min(0, enemy_army_torb_defense - ally_army_torb_attack),0)
                enemy_army_torb.torb.adjust_hp(enemy_hp_adjust, context=f"defending against {self.colony.name}'s Army")
        
        if ally_hp_adjust > enemy_hp_adjust:
            self.adjust_morale(1)
            enemy_army_torb.army.adjust_morale(-1)
        else:
            self.adjust_morale(-1)
            enemy_army_torb.army.adjust_morale(1)
    
    def adjust_morale(self, adjust_amount):
        self.morale = max(0, min(100, self.morale + adjust_amount))
        self.save()

    def _attack_successful(self, enemy_colony):
        stolen_food_amount = 0
        
        min_steal_amount = min(enemy_colony.food, round(self.army_power))
        
        if enemy_colony.food > 0:
            stolen_food_amount = random.randrange(min_steal_amount, enemy_colony.food)
            self.colony.adjust_food(stolen_food_amount)
            enemy_colony.adjust_food(-1 * stolen_food_amount)
        StoryText.objects.create(
                colony=self.colony,
                story_text_type="combat",
                story_text=f"Your army had a glorious victory over {enemy_colony.name} and plundered {stolen_food_amount} food.",
                timestamp=Now(),
                )
        
        StoryText.objects.create(
                colony=enemy_colony,
                story_text_type="combat",
                story_text=f"We were ransacked by {self.colony.name} and they stole {stolen_food_amount} food.",
                timestamp=Now(),
                )
    
    def _attack_failed(self, enemy_colony):
        StoryText.objects.create(
                colony=self.colony,
                story_text_type="combat",
                story_text=f"Your army was defeated in a battle against {enemy_colony.name}.",
                timestamp=Now(),
                )
        
        StoryText.objects.create(
                colony=enemy_colony,
                story_text_type="combat",
                story_text=f"We successfully repelled an attack from {self.colony.name}.",
                timestamp=Now(),
                )

    # Helper scout methods

    def _scout_undefended_colony(self, colony_to_scout):
        self.colony.discovered_colonies.add(colony_to_scout)
        self.colony.save()
        StoryText.objects.create(
            colony=self.colony,
            story_text_type="scout",
            story_text=f"Your scout found {colony_to_scout.name} and they reported that it appears undefended.",
            timestamp=Now(),
        )

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
    torb = models.ForeignKey('main_game.Torb', on_delete=models.CASCADE, related_name='army_torb')
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