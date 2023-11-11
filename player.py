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
        
    Class Attributes:
        _instances (dict[int, Player]): Stores all Player instances with their PID as keys
    """
    
    _instances: dict[int, Player] = {}

    def __init__(self, PID: int, name: str = None) -> None:
        """
        Initializes a new Player instance.

        Args:
            PID (int): Unique Player ID, should be Discord User ID once in deployment
        """
        
        self.PID: int = PID
        self.colonies: dict[int, Colony] = {}
        self.name = name
        self.hide_dead = False
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
            self.colonies[CID] = (Colony._instances[CID])
            logging.debug(f"{self.log_head()}: Assigned colony {CID} - {Colony._instances[CID].name}")
        else:
            raise PlayerException("Cannot claim non-existant colony")
        return
    
    def train_soldiers(self, CID: int, torbs: str) -> None:
        """
        Enlists Torbs into the army of selected Colony.

        Args:
            CID (int): Colony ID to search for Torbs given
            torbs (str): List of Torbs in string format
        """
        
        logging.debug(f"{self.log_head()}: Player calling train_soldiers with torbs {torbs[:16]}")
        
        torbs_parsed = self.torb_string_regex(torbs)
        found_torbs = [self.find_torb(CID, torb[0], torb[1]) for torb in torbs_parsed]
        Colony._instances[CID].train_soldier(found_torbs)
        return len(found_torbs)
    
    def discharge_soldiers(self, CID: int, torbs: str) -> None:
        """
        Discharges Torbs from the army of selected Colony.

        Args:
            CID (int): Colony ID to search for Torbs given
            torbs (str): List of Torbs in string format
        """
        
        logging.debug(f"{self.log_head()}: Player calling discharge_soldiers with torbs {torbs[:16]}")
        
        torbs_parsed = self.torb_string_regex(torbs)
        found_torbs = [self.find_torb(CID, torb[0], torb[1]) for torb in torbs_parsed]
        Colony._instances[CID].discharge_soldier(found_torbs)
        return len(found_torbs)
    
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
        if found_torbs == False:
            raise PlayerException("Could not find Torbs.")
        
        colony = Colony._instances[CID]
        out_string = f"{colony.name} | Food: {colony.food} | "
        out_string += f"Living Torbs: {len([torb for ID, torb in colony.torbs.items() if torb.alive])} | "
        out_string += f"Dead Torbs: {len([torb for ID, torb in colony.torbs.items() if not torb.alive])}\n"
        out_string += "`TORB GEN-ID     CURRENT/MAX HP    CONSTITUTION   DEFENSE   AGILITY    STRENGTH`"

        if self.hide_dead == True:
            found_torbs = [torb for torb in found_torbs if torb.alive]
        
        for torb in found_torbs:
            id_str = str(f"{torb.ID:02d}") + ""
            gen_str = str(f"{torb.generation:02d}") + ""
            assert isinstance(torb.ID, int), f"torb.ID is not an int: {type(torb.ID)}"
            assert isinstance(torb.generation, int), f"torb.generation is not an int: {type(torb.generation)}"
            out_string += "\n\n"
            status_effects = 0
            if torb in torb.colony.breeding:
                out_string += ":busts_in_silhouette: "
                status_effects += 1
            if torb in torb.colony.growing:
                out_string += ":baby_bottle: "
                status_effects += 1
            if torb in torb.colony.soldiers:
                out_string += ":military_helmet: "
                status_effects += 1
            if torb in torb.colony.training:
                out_string += ":dart: "
                status_effects += 1
            if torb in torb.colony.resting:
                out_string += ":pill: "
                status_effects += 1
            if torb.starving:
                out_string += ":bone: "
                status_effects += 1
            if not torb.alive:
                out_string += ":headstone: "
            spacer = "       "
            if status_effects == 0:
                out_string += spacer * 2
            elif status_effects == 1:
                out_string += spacer
            
            out_string += (f"**Colony {torb.colony.name}** - Torb `{gen_str}-{id_str}`:   ")
            out_string += (f":mending_heart:[`{torb.hp:.2f}/{torb.max_hp:.2f}`]   Genes:  ")
            out_string += (f":two_hearts:[`{torb.health.get_allele(0):.2f}|{torb.health.get_allele(1):.2f}`]   ")
            out_string += (f":shield:[`{torb.defense.get_allele(0):.2f}|{torb.defense.get_allele(1):.2f}`]   ")
            out_string += (f":zap:[`{torb.agility.get_allele(0):.2f}|{torb.agility.get_allele(1):.2f}`]   ")
            out_string += (f":muscle:[`{torb.strength.get_allele(0):.2f}|{torb.strength.get_allele(1):.2f}`]   ")
            
        #logging.debug(f"{self.log_head()}: {out_string}")
        logging.debug(f"{self.log_head()}: Viewing Colony {Colony._instances[CID].name} torbs")
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
        logging.debug(f"{self.log_head()}: Parsing input torb string")
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
        for _, colony in Colony._instances.items():
            logging.debug(f"{self.log_head()}: Checking colony {colony.CID:02d} against {CID:02d}")
            if colony.CID == CID:
                logging.debug(f"{self.log_head()}: Found colony {colony.CID:02d} {colony.name}")
                sel_colony = colony
                
        if sel_colony == None:
            logging.debug(f"{self.log_head()}: Could not find colony")
            return False
        
        for _, torb in sel_colony.torbs.items():
            if torb.generation in gen and torb.ID == ID:
                logging.debug(f"{self.log_head()}: Found torb {torb.generation:02d}-{torb.ID:02d}")
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

        logging.debug(f"{self.log_head()}: Attempting to scout all colonies from CID {CID}")
        from story_strings import player_strings
        
        if len(Colony._instances[CID].soldiers) == 0 and len(Colony._instances[CID].training) > 0:
            return f"Our soldiers are still training, {player_strings(self.name)}."
        elif len(Colony._instances[CID].soldiers) == 0:
            return f"We cannot scout without an army, {player_strings(self.name)}."
        
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

        out_str = f"{player_strings(self.name)}, your scouts have returned with the following info:\n"
        foreign_army_info = self.colonies[CID].scout_all_colonies()
        if foreign_army_info == False:
            return "You have the only army in all the lands."
        for foreign_colony, (hp, power, resil) in foreign_army_info.items():
            hp_str = describe_stat(hp, hp_thresholds, hp_descriptions)
            power_str = describe_stat(power, power_thresholds, power_descriptions)
            resil_str = describe_stat(resil, resil_thresholds, resil_descriptions)
            if hp == 0:
                out_str += f"{foreign_colony}'s Army: Does not exist\n"
            else:
                out_str += f"{foreign_colony}'s Army: {hp_str}, {power_str}, and {resil_str}\n"
        return out_str

    def ready_up(self, CID: int) -> None:
        """
        Sets the given Colony's ready status to True.

        Args:
            CID (int): ID of the Colony to set to ready
        """
        
        logging.info(f"{self.log_head()}: Colony {Colony._instances[CID].name} readied up")
        Colony._instances[CID].ready = True
        
        from story_strings import random_event
        out = random_event()
        return out

    def set_target(self, CID: int, target_colony: str) -> bool:
        """
        Searches for matching Colony and sets it as owned Colony's target.

        Args:
            CID (int): Owned Colony's ID
            target_colony (str): String of the name of desired target Colony

        Returns:
            bool: Whether a valid target Colony was found
        """
        
        search_text = target_colony.strip()
        for target_CID, colony in Colony._instances.items():
            if colony.name == search_text:
                Colony._instances[CID].attack_target = target_CID
                logging.debug(f"{self.log_head()}: Colony {Colony._instances[CID].name} chose {colony.name} as its target")
                return True
        logging.info(f"{self.log_head()}: Couldn't find Colony {search_text[:10]}")
        return False



    def log_head(self) -> str:
        """
        Generates a standard log header for the Player.

        Returns:
            str: Formatted log header string
        """
        
        return f"PID-{self.name[:10]}"