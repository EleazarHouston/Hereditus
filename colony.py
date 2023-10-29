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
        generations (int): Number of generations that exist in the Colony
        torbs (dict): Dictionary storing Torbs, with the Torb count as keys and Torb objects as values
        torb_count (int): Total count of Torbs in the Colony
        at_arms (list[Torb]): List of Torbs that are ready for battle.
        breeding (list[Torb]): List of Torbs that are currently breeding
        food (int): Current amount of food available to the Colony
        scouts (int): Count of Torbs that are ready to scout

    Class Attributes:
        _instances (dict): Stores all Colony instances with their CID as keys
        _next_CID (int): The next available CID
    """
    
    _instances: dict[int, Colony] = {}
    _next_CID: int = 0
    
    def __init__(self, CID: int, name: str, EEID: int, PID: int = None) -> None:
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
        Colony._instances[self.CID] = self
        Colony._next_CID += 1
        self.at_arms: list[Torb] = []
        self.breeding: list[Torb] = []
        self.food: int = 5
        self.scouts: int = 0
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
            new_torb = Torb(i, 0, self.CID, EEID=self.EE.EEID)
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
        
        self.generations += 1
        logging.debug(f"{self.log_head()}: Breeding generation {self.generations} with pairs {pairs}")
        for i, pair in enumerate(pairs):
            child_genes = self.EE.breed_parents(pair)
            if child_genes == False:
                continue
            logging.debug(f"{self.log_head()}: Child genes {child_genes} generated")
            child = Torb(i, self.generations, self.CID, parents = pair, genes = child_genes, EEID = self.EE.EEID)
            self.torbs[self.torb_count] = child
            self.torb_count += 1
        logging.info(f"{self.log_head()}: Generation {self.generations} generated")
        return
    
    def battle_ready(self, torbs: list) -> None:
        """
        Enlists Torbs for battle if they are eligible.
        
        Args:
            torbs (list): List of Torbs to be checked and enlisted for battle
        """
        
        for torb in torbs:
            if torb.hp != 0 and torb.alive and torb not in self.breeding and isinstance(torb, Torb):
                self.at_arms.append(torb)
                self.scouts += 1
            else:
                logging.warning(f"{self.log_head()}: Torb {torb.UUID} {torb.gen}-{torb.ID} is not a valid soldier candidate.")
                #TODO This should raise an exception that is caught and communicated to player
        return
    
    def gather(self) -> None:
        """
        Gathers food for the colony based on available Torbs.
        """
        
        living_torbs = [torb for torb in self.torbs if torb.alive]
        num_torbs = len(living_torbs)
        num_breeding = len(self.breeding)
        num_guarding = len(self.at_arms)
        num_gathering = num_torbs - num_breeding - num_guarding
        self.food += num_gathering
        #Maybe add differing amounts based on gathering torb genes: strength?
        return
        
    def colony_meal(self) -> None:
        """
        Feeds the colony and handle starvation if necessary.
        """
        
        living_torbs = [torb for torb in self.torbs.values() if torb.alive]
        starved_torbs = []

        if self.food < len(living_torbs):
            starved_torbs = random.sample(living_torbs, len(living_torbs) - self.food)
            for torb in starved_torbs:
                torb.adjust_hp(-1)

        for torb in living_torbs:
            if torb not in starved_torbs:
                torb.adjust_hp(1)
                
        self.food -= len(living_torbs)
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
        
        self.scouts = 0
        self.at_arms = []
        self.breeding = []
        for torb in self.torbs:
            torb.fertile = True
        return
    
    def at_arms_info(self) -> ArmyStats:
        """
        Provides detailed stats about the colony's standing army.
        
        Returns:
            list: Combined army's average strength, agility, constitution, defense, hp, max_hp
        """
        
        real_average_strength = 0
        real_average_agility = 0
        real_average_constitution = 0
        real_average_defense = 0
        real_current_hp = 0
        real_max_hp = 0
        
        for soldier in self.at_arms:
            real_average_strength += np.average(soldier.strength.alleles)
            real_average_agility += np.average(soldier.agility.alleles)
            real_average_constitution += np.average(soldier.health.alleles)
            real_average_defense += np.average(soldier.defense.alleles)
            real_current_hp += soldier.hp
            real_max_hp += soldier.max_hp
            
        return ArmyStats(real_average_strength, real_average_agility, real_average_constitution, real_average_defense, real_current_hp, real_max_hp)
    
@dataclass
class ArmyStats:
    average_strength: float
    average_agility: float
    average_constitution: float
    average_defense: float
    current_hp: float
    max_hp: float