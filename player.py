from __future__ import annotations

import logging
import re

from colony import Colony
from evolution_engine import EvolutionEngine
from exceptions import *
from torb import Torb

logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class Player:
    """
    Calls relevant game functions per player input.

    Attributes:
        PID (int): Unique Player ID
        colonies (list): List of associated Colonies
        colony_count (int): Number of colonies controlled by this Player
        
    Class Attributes:
        _instances (dict[int, Player]): Stores all Player instances with their PID as keys
    """
    
    _instances: dict[int, Player] = {}

    def __init__(self, PID: int) -> None:
        """
        Initializes a new Player instance.

        Args:
            PID (int): Unique Player ID, should be Discord User ID once in deployment
        """
        
        self.PID: int = PID
        self.colonies: dict[int, Colony] = {}
        self.colony_count: int = 0
        Player._instances[PID] = self
        logging.info(f"{self.log_head()}: Initialization successful")
        return
    
    def assign_colony(self, CID: int) -> None:
        """
        Assigns a Colony to the Player instance.

        Args:
            CID (int): ID of the Colony to be assigned

        Raises:
            PlayerException: When trying to claim a non-existant colony
        """
        
        if CID in Colony._instances:
            Colony._instances[CID].PID = self.PID
            self.colonies[self.colony_count]=(Colony._instances[CID])
            self.colony_count += 1
            logging.debug(f"{self.log_head()}: Assigned colony {self.colony_count-1}")
        else:
            raise PlayerException("Cannot claim non-existant colony")
        return
    
    def send_to_arms(self, CID: int, torbs: str) -> None:
        """
        Enlists Torbs into the army of selected Colony.

        Args:
            CID (int): Colony ID to search for Torbs given
            torbs (str): List of Torbs in string format
        """
        
        torb_parsed = self.torb_string_regex(torbs)
        Colony._instances[CID].battle_ready(torb_parsed)
        return
    
    def view_torbs(self, CID: int, generations: int | list = [0,99]) -> str:
        """
        Generates a readable string of info from the selected Torbs.

        Args:
            CID (int): Colony ID to send the command to
            generations (int | list, optional): Torb generation(s) to view, defaults to [0,99].

        Returns:
            str: Torb info in format Colony <name> - Torb <gen>-<ID> <hp>/<max_hp> Genes: <health> <defense> <agility> <strength>
        """
        
        if generations == [0, 99]:
            generations = list(range(generations[0], generations[1]))
        if type(generations) == int:
            generations = [generations]
        
        found_torbs = self.find_torb(CID, generations, "any")
        out_string = "`COLONY " + " " * len(Colony._instances[CID].name) + "TORB GEN-ID  CURRENT/MAX HP    CONSTITUTION   DEFENSE   AGILITY    STRENGTH`"
        
        for torb in found_torbs:
            out_string += (f"\n\n**Colony {torb.colony.name}** - Torb `{torb.generation:02d}-{torb.ID:02d}`:   "
            f":mending_heart:[`{torb.hp:02d}/{torb.max_hp:02d}`]   Genes:  "
            f":two_hearts:[`{torb.health.get_allele(0):02}|{torb.health.get_allele(1):02d}`]   "
            f":shield:[`{torb.defense.get_allele(0):02d}|{torb.defense.get_allele(1):02d}`]   "
            f":zap:[`{torb.agility.get_allele(0):02d}|{torb.agility.get_allele(1):02d}`]   "
            f":muscle:[`{torb.strength.get_allele(0):02d}|{torb.strength.get_allele(1):02d}`]   "
            )
            
        logging.debug(f"{self.log_head()}: {out_string}")
        logging.debug(f"{self.log_head()}: Viewing {CID} torbs")
        return out_string

    def call_colony_reproduction(self, CID: int, pairs: str) -> None:
        """
        Requests Colony reproduction given Colony ID and breeding pairs.

        Args:
            CID (int): Colony ID to search for Torbs given
            pairs (str): String representation of pairs to be bred together

        Raises:
            PlayerException: When number of Torbs given is not divisible by 2
        """
        
        logging.debug(f"{self.log_head()}: Calling colony reproduction in colony {CID}")
        breeding_list = []
        if pairs == "":
            pairs = "00-00, 00-01"

        breeding_torbs_info = self.torb_string_regex(pairs)
        if len(breeding_torbs_info)%2 != 0:
            raise PlayerException(f"Asked to breed invalid number {len(breeding_torbs_info)} of torbs")
        out_pairs = []
        for i in range(0, len(breeding_torbs_info)//2):
            out_pair = []
            parent1 = self.find_torb(CID, breeding_torbs_info[2*i][0], breeding_torbs_info[2*i][1])
            parent2 = self.find_torb(CID, breeding_torbs_info[2*i+1][0], breeding_torbs_info[2*i+1][1])
            print(parent1.UID)
            out_pair = [parent1, parent2]
            out_pairs.append(out_pair)
            
            self.colonies[CID].colony_reproduction(out_pairs)
            
        logging.info(f"{self.log_head()}: Player requested breeding complete in colony {CID}")
        return
    
    def torb_string_regex(self, torb_str: str) -> list[str]:
        """
        Parses a string to extract Torb generation and ID.

        Args:
            torb_str (str): String identifying Torb in form similar to '<gen>-<ID>', e.g., '00-04'

        Returns:
            list[str]: A list containing parsed Torb generation and ID, e.g., ['00', '04']
        """
        
        pattern0 = r"\d{1,2}\s*[-]\s*\d{1,2}"
        pattern1 = r"\d{1,2}"
        
        torb_list = re.findall(pattern0, torb_str)
        out_torb_list = []
        for torb_info in torb_list:
            out_torb_list.append(re.findall(pattern1, torb_info))
        
        return out_torb_list
    
    def find_torb(self, CID: int, gen: int|list, ID: int|str) -> list[Torb] | Torb:
        """
        Searches given Colony for identified Torb.

        Args:
            CID (int): Colony ID (CID) to be searched
            gen (int | list): Generation of Torb to be found
            ID (int | str): ID of Torb to be found

        Returns:
            list[Torb] | Torb: Returns list of found Torbs or single found Torb
        """
        
        logging.debug(f"{self.log_head()}: Finding torb {gen}-{ID}")
        sel_colony = None
        out = False
        
        if type(gen) != list:
            gen = [int(gen)]
        if ID != "any":
            ID = int(ID)
            logging.debug(f"{self.log_head()}: Finding all torbs in gen {gen}")
        logging.debug(f"{self.log_head()}: gen: {gen}, ID: {ID}")
        out_torbs = []
        for CID, colony in Colony._instances.items():
            logging.debug(f"{self.log_head()}: Checking colony {colony.CID} against {CID}")
            if colony.CID == CID:
                logging.debug(f"{self.log_head()}: Found colony {colony.CID} {colony.name}")
                sel_colony = colony
                
        if sel_colony == None:
            return False
        
        for UID, torb in sel_colony.torbs.items():
            if torb.generation in gen and torb.ID == ID:
                logging.debug(f"{self.log_head()}: Found torb {torb.gen}-{torb.ID}")
                return torb
            elif torb.generation in gen and ID == "any":
                out_torbs.append(torb)
                out = out_torbs
        return out
        
    def scout_all(self, CID: int) -> str:
        """
        Returns a string describing the stats of all armies compared to this Colony's army.

        Args:
            CID (int): ID of the scouting Colony

        Returns:
            str: Player-readable string describing each Colony in comparison to their own
        """

        def describe_stat(value, thresholds, descriptions):
            for threshold, desc in zip(thresholds, descriptions):
                if value > threshold:
                    return desc
            return descriptions[-1]

        hp_thresholds = [0.95, 0.7, 0.4, 0]
        hp_descriptions = [
            "seems uninjured",
            "is lightly injured",
            "appear moderately injured",
            "looks like it's on the brink of collapse"
        ]

        power_thresholds = [1.4, 1.15, 0.85, 0.5, 0]
        power_descriptions = [
            "appears much stronger than our army",
            "seems somewhat stronger than our army",
            "looks about the same strength as ours",
            "is moderately weaker than ours",
            "is much weaker than our army"
        ]

        resil_thresholds = [1.4, 1.15, 0.85, 0.5, 0]
        resil_descriptions = [
            "appears much more resilient than ours",
            "seems somewhat more resilient than our army",
            "looks just as resilient as ours",
            "is moderately less resilient than ours",
            "is much less resilient than our army"
        ]

        out_str = ""
        foreign_army_info = self.colonies[CID].scout_all_colonies()
        for foreign_colony, (hp, power, resil) in foreign_army_info:
            hp_str = describe_stat(hp, hp_thresholds, hp_descriptions)
            power_str = describe_stat(power, power_thresholds, power_descriptions)
            resil_str = describe_stat(resil, resil_thresholds, resil_descriptions)
            
            out_str += f"{foreign_colony}'s Army: {hp_str}, {power_str}, and {resil_str}\n"
        return out_str

        
    
    def log_head(self) -> str:
        """
        Generates a standard log header for the Player.

        Returns:
            str: Formatted log header string
        """
        
        return f"PID-{self.PID:02d}"