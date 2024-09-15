from django.db import models
import random

class Army(models.Model):
    from .torb import Torb
    colony = models.OneToOneField('main_game.Colony', on_delete=models.CASCADE, related_name='army_instance')
    #torbs = models.ManyToManyField('main_game.Torb')
    
    @property
    def army_health(self):
        return sum(army_torb.torb.hp for army_torb in self.army_torbs.all())
    
    @property
    def army_power(self):
        return sum(army_torb.power for army_torb in self.army_torbs.all())
    
    @property
    def army_resilience(self):
        return sum(army_torb.resilience for army_torb in self.army_torbs.all())
    

# Makes sense to have ArmyTorb in same file as Army
class ArmyTorb(models.Model):
    army = models.ForeignKey('main_game.Army', on_delete=models.CASCADE, related_name='army_torbs')
    torb = models.ForeignKey('main_game.Torb', on_delete=models.CASCADE)
    active_alleles = models.JSONField(default=dict)
    
    @property
    def power(self):
        return round((self.active_alleles['strength'] * self.active_alleles['agility']**0.5), 2)
    
    @property
    def resilience(self):
        return round((self.active_alleles['vitality'] * self.active_alleles['sturdiness']**0.5), 2)
    
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
            strength_allele=strength_allele,
            agility_allele=agility_allele,
            vitality_allele=vitality_allele,
            sturdiness_allele=sturdiness_allele
        )

    def remove_from_army(self):
        self.delete()