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
    
    def send_to_arms(self, colony_ID: int, torbs: str) -> None:
        """
        Enlists Torbs into the army of selected Colony.

        Args:
            colony_ID (int): Colony ID to search for Torbs given
            torbs (str): List of Torbs in string format
        """
        
        torb_parsed = self.torb_string_regex(torbs)
        Colony._instances[colony_ID].battle_ready(torb_parsed)
        return
    
    def view_torbs(self, colony_ID: int, generations: int | list = [0,99]) -> str:
        """
        Generates a readable string of info from the selected Torbs.

        Args:
            colony_ID (int): Colony ID to send the command to
            generations (int | list, optional): Torb generation(s) to view, defaults to [0,99].

        Returns:
            str: Torb info in format Colony <name> - Torb <gen>-<ID> <hp>/<max_hp> Genes: <health> <defense> <agility> <strength>
        """
        
        if generations == [0, 99]:
            generations = list(range(generations[0], generations[1]))
        if type(generations) == int:
            generations = [generations]
        
        found_torbs = self.find_torb(colony_ID, generations, "any")
        out_string = "`COLONY " + " " * len(Colony._instances[colony_ID].name) + "TORB GEN-ID  CURRENT/MAX HP    CONSTITUTION   DEFENSE   AGILITY    STRENGTH`"
        
        for torb in found_torbs:
            out_string += (f"\n\n**Colony {torb.colony.name}** - Torb `{torb.generation:02d}-{torb.ID:02d}`:   "
            f":mending_heart:[`{torb.hp:02d}/{torb.max_hp:02d}`]   Genes:  "
            f":two_hearts:[`{torb.health.get_allele(0):02}|{torb.health.get_allele(1):02d}`]   "
            f":shield:[`{torb.defense.get_allele(0):02d}|{torb.defense.get_allele(1):02d}`]   "
            f":zap:[`{torb.agility.get_allele(0):02d}|{torb.agility.get_allele(1):02d}`]   "
            f":muscle:[`{torb.strength.get_allele(0):02d}|{torb.strength.get_allele(1):02d}`]   "
            )
            
        logging.debug(f"{self.log_head()}: {out_string}")
        logging.debug(f"{self.log_head()}: Viewing {colony_ID} torbs")
        return out_string

    def call_colony_reproduction(self, colony_ID: int, pairs: str) -> None:
        """
        Requests Colony reproduction given Colony ID and breeding pairs.

        Args:
            colony_ID (int): Colony ID to search for Torbs given
            pairs (str): String representation of pairs to be bred together

        Raises:
            PlayerException: When number of Torbs given is not divisible by 2
        """
        
        logging.debug(f"{self.log_head()}: Calling colony reproduction in colony {colony_ID}")
        breeding_list = []
        if pairs == "":
            pairs = "00-00, 00-01"

        breeding_torbs_info = self.torb_string_regex(pairs)
        if len(breeding_torbs_info)%2 != 0:
            raise PlayerException(f"Asked to breed invalid number {len(breeding_torbs_info)} of torbs")
        out_pairs = []
        for i in range(0, len(breeding_torbs_info)//2):
            out_pair = []
            parent1 = self.find_torb(colony_ID, breeding_torbs_info[2*i][0], breeding_torbs_info[2*i][1])
            parent2 = self.find_torb(colony_ID, breeding_torbs_info[2*i+1][0], breeding_torbs_info[2*i+1][1])
            print(parent1.UID)
            out_pair = [parent1, parent2]
            out_pairs.append(out_pair)
            
            self.colonies[colony_ID].colony_reproduction(out_pairs)
            
        logging.info(f"{self.log_head()}: Player requested breeding complete in colony {colony_ID}")
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
    
    def find_torb(self, colony_ID: int, gen: int|list, ID: int|str) -> list[Torb] | Torb:
        """
        Searches given Colony for identified Torb.

        Args:
            colony_ID (int): Colony ID (CID) to be searched
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
            logging.debug(f"{self.log_head()}: Checking colony {colony.CID} against {colony_ID}")
            if colony.CID == colony_ID:
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
    
    def log_head(self) -> str:
        """
        Generates a standard log header for the Player.

        Returns:
            str: Formatted log header string
        """
        
        return f"PID-{self.PID:02d}"