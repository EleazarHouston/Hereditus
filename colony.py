from __future__ import annotations
from dataclasses import dataclass
import logging
import random

import numpy as np

from evolution_engine import EvolutionEngine
from exceptions import *
from torb import Torb

logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class Colony:
    """
    Represents a group of entities for the game's ecosystem.

    Attributes:
        CID (int): Unique Colony ID
        name (str): Name of the Colony
        EE (EvolutionEngine): Associated Evolution Engine instance
        PID (int): Player ID associated with the Colony, can be None
        SID (int): Simulator ID in charge of this Colony, can be None
        generations (int): Number of generations that exist in the Colony
        torbs (dict[int, Torb]): Dictionary storing Torbs, with the Torb count as keys and Torb objects as values
        torb_count (int): Total count of Torbs in the Colony
        at_arms (list[Torb]): List of Torbs that are ready for battle.
        breeding (list[Torb]): List of Torbs that are currently breeding
        food (int): Current amount of food available to the Colony
        scouts (int): Count of Torbs that are ready to scout
        ready (bool): Whether the Colony has done all actions for the round or not
        destroyed (bool): Whether the Colony is destroyed or not
    Class Attributes:
        _instances (dict[int, Colony]): Stores all Colony instances with their CID as keys
        _next_CID (int): The next available CID
    """
    
    _instances: dict[int, Colony] = {}
    _next_CID: int = 0
    
    def __init__(self, CID: int, name: str, EEID: int, PID: int = None, SID: int = None) -> None:
        """
        Initializes a new Colony instance.
        
        Args:
            CID (int): Unique Colony ID
            name (str): Name of the Colony
            EEID (int): Evolution Engine ID associated with the Colony
            PID (int, optional): Player ID associated with the Colony, defaults to None
        """
        
        self.CID: int = CID
        self.name: str = name
        self.EE: EvolutionEngine = EvolutionEngine._instances[EEID]
        self.generations: int = 0
        self.torbs: dict[int, Torb] = {}
        self.torb_count: int = 0
        self.PID: int = PID
        self.SID: int = SID
        Colony._instances[self.CID] = self
        Colony._next_CID += 1
        self.at_arms: list[Torb] = []
        self.training: list[Torb] = []
        self.soldiers: list[Torb] = []
        self.breeding: list[Torb] = []
        self.resting: list[Torb] = []
        self.growing: list[Torb] = []
        self.food: int = 5
        self.scouts: int = 0
        self.ready: bool = False
        self.destroyed: bool = False
        self.attack_target = None
        logging.info(f"{self.log_head()}: Successfully initialized: PID {self.PID}")
        return
    
    def init_gen_zero(self, num_torbs: int) -> None:
        """
        Initializes generation zero with a specified number of Torbs
        
        Args:
            num_torbs (int): Number of Torbs to generate for generation zero
        """
        
        if self.generations != 0:
            logging.warning(f"{self.log_head()}: There are already {self.generations} generations")
            return
        logging.debug(f"{self.log_head()}: Generating generation 0")
        for i in range(num_torbs):
            new_torb = self.EE.create_torb(ID = i, generation = 0, CID = self.CID)
            self.torbs[self.torb_count] = new_torb
            self.torb_count += 1
        logging.debug(f"{self.log_head()}: Generation 0 initialized")
        return

    def colony_reproduction(self, pairs: list) -> None:
        """
        Carries out reproduction for the specified Torb pairs to generate a new generation.
        
        Args:
            pairs (list): A list of lists where each sublist is a pair of Torbs to breed
        """
        
        logging.debug(f"{self.log_head()}: Reproducing the colony")
        self.generations += 1
        logging.debug(f"{self.log_head()}: Breeding generation {self.generations:02d} with pairs {pairs}")
        for i, pair in enumerate(pairs):
            if pair[0] in self.training or pair[0] in self.soldiers:
                raise ColonyException(f"{pair[0].generation:02d}-{pair[0].ID:02d} is on active duty and cannot breed.")
            if pair[1] in self.training or pair[1] in self.soldiers:
                raise ColonyException(f"{pair[1].generation:02d}-{pair[1].ID:02d} is on active duty and cannot breed.")
            
            if pair[0] in self.breeding or pair[0] in self.growing:
                raise ColonyException(f"{pair[0].generation:02d}-{pair[0].ID:02d} is busy being a part of a new family.")
            if pair[1] in self.breeding or pair[1] in self.growing:
                raise ColonyException(f"{pair[1].generation:02d}-{pair[1].ID:02d} is busy being a part of a new family.")
            
            self.breeding += pair
            child = self.EE.create_torb(ID = i, generation = self.generations, CID = self.CID, parents=pair)
            self.torbs[self.torb_count] = child
            self.growing.append(child)
            self.torb_count += 1
            
        logging.info(f"{self.log_head()}: Generation {self.generations:02d} generated")
        return
    
    def train_soldier(self, torbs: list) -> None:
        """
        Enlists Torbs for battle if they are eligible.
        
        Args:
            torbs (list): List of Torbs to be checked and enlisted for battle
        """
        
        logging.debug(f"{self.log_head()}: Readying Torbs for battle in {self.name}")
        for torb in torbs:
            if torb in self.soldiers or torb in self.training:
                raise ColonyException("Cannot train a Torb already enlisted.")
            elif torb.hp != 0 and torb.alive and torb not in self.breeding and isinstance(torb, Torb) and torb not in self.growing:
                self.training.append(torb)
                self.scouts += 1
            else:
                raise ColonyException(f"Torb {torb.generation}-{torb.ID} is not a valid soldier candidate.")
        logging.debug(f"{self.log_head()}: {len(torbs)} enlisted.")
        return
    
    def discharge_soldier(self, torbs: list) -> None:
        """
        Discharges Torbs from standing army.
        
        Args:
            torbs (list): List of Torbs to be discharged.
        """
        
        logging.debug(f"{self.log_head()}: Discarging Torbs from army in {self.name}")
        for torb in torbs:
            if not torb.alive:
                raise ColonyException("Can't discharge deceased.")
            elif torb not in self.soldiers and torb not in self.training:
                raise ColonyException("Soldier not found.")
            else:
                if torb in self.soldiers:
                    self.soldiers -= torb
                else:
                    self.training -= torb
        logging.debug(f"{self.log_head()}: {len(torbs)} enlisted.")
        return
    
    def gather(self) -> None:
        """
        Gathers food for the colony based on available Torbs.
        """
        
        living_torbs = [torb for UID, torb in self.torbs.items() if torb.alive]
        num_torbs = len(living_torbs)
        num_breeding = len(self.breeding)
        num_soldiers = len(self.soldiers)
        num_training = len(self.training)
        num_growing = len(self.growing)
        num_gathering = num_torbs - num_breeding - num_soldiers - num_training - num_growing
        self.food += round(num_gathering * 1.6)
        #Maybe add differing amounts based on gathering torb genes: strength?
        return
        
    def colony_meal(self) -> None:
        """
        Feeds the colony and handle starvation if necessary.
        """
        
        living_torbs = [torb for UID, torb in self.torbs.items() if torb.alive]
        starved_torbs = []

        if self.food < len(living_torbs):
            starved_torbs = random.sample(living_torbs, len(living_torbs) - self.food)
            for torb in starved_torbs:
                torb.starving = True
                torb.adjust_hp(-1)

        for torb in living_torbs:
            if torb not in starved_torbs:
                torb.starving = False
                torb.adjust_hp(1)
                
        self.food -= len(living_torbs)
        self.food = max(self.food, 0)
        return

    def log_head(self) -> str:
        """
        Generates a standard log header for the Colony.
        
        Returns:
            str: Formatted log header string
        """
        
        return f"CID-{self.CID:02d} Colony {self.name:>8}"

    def new_round(self) -> None:
        """
        Prepares the colony for a new round.
        """
        
        self.scouts = len(self.soldiers)
        for UID, torb in self.torbs.items():
            torb.fertile = True if torb.alive else False
        for torb in self.resting:
            if not torb.starving:
                torb.adjust_hp(3)
    
        self.ready = False
        return
    
    def initiate_soldiers(self):
        new_soldiers = [torb for torb in self.training if torb.alive and not torb.starving]
        self.soldiers += new_soldiers
        for soldier in new_soldiers:
            self.training.remove(soldier)
        return
    
    def army_info(self) -> ArmyStats:
        """
        Provides detailed stats about the colony's standing army.
        
        Returns:
            ArmyStats: Combined army's strength, agility, constitution, defense, hp, max_hp
        """
        
        real_average_strength = 0
        real_average_agility = 0
        real_average_constitution = 0
        real_average_defense = 0
        real_current_hp = 0
        real_max_hp = 0
        
        for soldier in self.soldiers:
            real_average_strength += np.average(soldier.strength.alleles)
            real_average_agility += np.average(soldier.agility.alleles)
            real_average_constitution += np.average(soldier.health.alleles)
            real_average_defense += np.average(soldier.defense.alleles)
            real_current_hp += soldier.hp
            real_max_hp += soldier.max_hp
            
        return ArmyStats(real_average_strength, real_average_agility, real_average_constitution, real_average_defense, real_current_hp, real_max_hp)
    
    def scout_all_colonies(self) -> dict[str, tuple[float, float, float]]:
        """
        Returns statistics for ecah colony in the game, compared to this colony.

        Returns:
            dict[str, tuple[float, float, float]]: A dictionary where the key is the Colony name, 
            and the values are a tuple of the foreign army's hp percentage, comparative power, and comparative resilience.
        """
        logging.debug(f"{self.log_head()}: Scouting all known colonies")
        # This is inefficient when multiple colonies/players call global_scout(), consider storing and re-using per round
        from simulator import Simulator
        global_scout_info = Simulator._instances[self.SID].global_scout()
        my_army_stats = self.army_info()
        my_power = my_army_stats.army_strength + my_army_stats.army_agility
        my_resilience = my_army_stats.army_constitution + my_army_stats.army_defense

        
        compar_army_stats = {}
        logging.info(f"{self.log_head()}: Known colonies == {len(global_scout_info)}")
        if len(global_scout_info) == 1:
            return False
        for foreign_colony, foreign_stats in global_scout_info.items():
            if foreign_colony == self.name:
                continue
            try:
                foreign_army_power = foreign_stats.army_strength + foreign_stats.army_agility
                foreign_army_resilience = foreign_stats.army_constitution + foreign_stats.army_defense
                foreign_army_rel_hp = foreign_stats.army_hp / foreign_stats.army_max_hp
            except ZeroDivisionError:
                foreign_army_power = 0
                foreign_army_resilience = 0
                foreign_army_rel_hp = 0
            
            compare_power = foreign_army_power / my_power
            compare_resilience = foreign_army_resilience / my_resilience
            compar_army_stats[foreign_colony] = foreign_army_rel_hp, compare_power, compare_resilience
            
        return compar_army_stats

    def rest(self, torbs: list[Torb]):
        for torb in torbs:
            if torb in self.breeding or torb in self.soldiers or torb in self.resting or torb.starving or torb in self.training:
                # Change to exception
                print("Torb cannot rest")
                continue
            if not torb.max_hp > torb.hp:
                print("Torb already max hp")
                continue
            self.resting.append(torb)
        return
    
@dataclass
class ArmyStats:
    army_strength: float
    army_agility: float
    army_constitution: float
    army_defense: float
    army_hp: float
    army_max_hp: float