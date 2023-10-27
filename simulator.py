import random
from math import sqrt
import logging
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class Simulator:
    _instances = {}
    _next_SID = 0
    
    def __init__(self, SID, battle_draw_chance = 0.02):
        self.SID = SID
        self.colonies = {}
        self.colony_count = 0
        self.battle_draw_chance = battle_draw_chance
        self.evolution_engines = {}
        self.started = False
        Simulator._instances[SID] = self
        Simulator._next_SID += 1
        logging.info(f"{self.log_head()}: Initialization successful")
        return
    
    def new_evolution_engine(self):
        from evolution_engine import EvolutionEngine
        self.evolution_engines[EvolutionEngine._next_EID] = EvolutionEngine(EvolutionEngine._next_EID)
        return
    
    def new_colony(self, name, EEID, PID):
        from colony import Colony
        from player import Player
        self.colonies[Colony._next_CID] = Colony(Colony._next_CID, name, EEID, PID)
        print("Assigning colony from Sim---")
        Player._instances[PID].assign_colony(self.colonies[Colony._next_CID].CID)
        self.colony_count += 1
        return
    
    def init_all_colonies(self, num_torbs):
        for CID, colony in self.colonies.items():
            colony.init_gen_zero(num_torbs)
        self.started = True
        return
    
    def scout(self):
        return
    
    def battle(self, col0: list, col1: list):
        army0 = col0.at_arms
        army1 = col1.at_arms
        while len(army0) > 0 and len(army1) > 0:
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
            torb0.adjust_hp(-impact_torb0)
        if impact_torb1 > 0:
            torb1.adjust_hp(-impact_torb1)
        return
    
    def next_round(self):
        for colony in self.colonies:
            colony.new_round()
            colony.gather()
            #Combat system
            colony.colony_meal()
        return
    
    def log_head(self):
        return f"SID-{self.SID:02d}"
    
    def global_scout(self, obscurity_level, adjust_factor = 0.75):
        """Give basic scouting information on every colony"""
        known_info = {}
        # Depending on how many colonies there are, this will be a very large output
        # Will need to add discord support for multiple pages in message or other form of compression
        for colony in self.colonies:
            exact_info = colony.at_arms_info()
            if obscurity_level == 0:
                given_info = exact_info
            elif obscurity_level == 1:
                adjusted_info = [info * (1 + random.uniform(-adjust_factor, adjust_factor)) for info in exact_info]
                given_info = adjusted_info
            elif obscurity_level == 2:
                a = 1
                # Not implemented yet, might give simple "above average, below average, etc."
            known_info[colony.name] = given_info
            
        # Should still be modified to conform to combined power and resilience, not gene level
        return known_info

    def specific_scout(self, target_colony_CID):
        # May add other things here later, hidden-ness of the target colony, etc.
        return self.colonies[target_colony_CID].at_arms_info()
        
        