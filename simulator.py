import random
from math import sqrt
import logging
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class Simulator:
    def __init__(self, SID, battle_draw_chance = 0.02):
        self.SID = SID
        self.colonies = {}
        self.colony_count = 0
        self.battle_draw_chance = battle_draw_chance
        self.evolution_engines = {}
        return
    
    def new_evolution_engine(self):
        from evolution_engine import EvolutionEngine
        self.evolution_engines[EvolutionEngine._next_EID] = EvolutionEngine()
        return
    
    def new_colony(self, name, EEID, PID):
        from colony import Colony
        self.colonies[Colony._next_CID] = Colony(Colony._next_CID, name, EEID, PID)
        self.colony_count += 1
        return
    
    def init_all_colonies(self, num_torbs):
        for CID, colony in self.colonies.items():
            colony.init_gen_zero(num_torbs)
        return
    
    def scout(self):
        return
    
    def battle(self, col0: list, col1: list):
        army0 = col0.at_arms
        army1 = col1.at_arms
        while army0 > 0 and army1 > 0:
            random.shuffle(army0)
            random.shuffle(army1)
            self.fight(army0[0], army1[0])
            if army0[0].alive == False:
                army0.pop(0)
            if army1[0].alive == False:
                army1.pop(0)
            draw_roll = random.uniform(0, 1)
            if draw_roll > (1-self.battle_draw_chance):
                break
        if len(army0) > 1:
            winner = col0
        elif len(army1) > 1:
            winner = col1
        else:
            winner = None
        return winner
    
    def fight(self, torb0, torb1):
        
        torb0_power = sqrt(torb0.strength.get_allele(is_random=True) * torb0.agility.get_allele(is_random=True))
        torb0_resilience = sqrt(torb0.health.get_allele(is_random=True) * torb0.defense.get_allele(is_random=True))
        torb1_power = sqrt(torb1.strength.get_allele(is_random=True) * torb1.agility.get_allele(is_random=True))
        torb1_resilience = sqrt(torb1.health.get_allele(is_random=True) * torb1.defense.get_allele(is_random=True))
        
        torb0_hit = random.randrange(1, torb0_power)
        torb0_protection = random.randrange(1, torb0_resilience)
        torb1_hit = random.randrange(1, torb1_power)
        torb1_protection = random.randrange(1, torb1_resilience)
        
        impact_torb0 = torb1_hit - torb0_protection
        impact_torb1 = torb0_hit - torb1_protection
        
        if impact_torb0 > 0:
            torb0.lower_hp(impact_torb0)
        if impact_torb1 > 0:
            torb1.lower_hp(impact_torb1)
        
        return
    
    def next_round(self):
        for colony in self.colonies:
            colony.gather()
            #Battle
            colony.colony_meal()
        return
    
    def log_head(self):
        return f"SID-{self.SID:02d}"
        