from colony import Colony
from exceptions import *
from evolution_engine import EvolutionEngine
from torb import Torb
import logging
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class Player:
    _instances = {}
    #Don't add _next_PID
    #PID = DiscordID
    def __init__(self, PID):
        self.PID = PID
        self.colonies = {}
        self.colony_count = 0
        Player._instances[PID] = self
        logging.info(f"{self.log_head()}: Initialization successful")
        return
    
    def assign_colony(self, CID):
        if CID in Colony._instances:
            Colony._instances[CID].PID = self.PID
            self.colonies[self.colony_count]=(Colony._instances[CID])
            self.colony_count += 1
            logging.debug(f"{self.log_head()}: Assigned colony {self.colony_count-1}")
        else:
            raise PlayerException("Cannot claim nonexistant colony")
        return
    
    def send_to_arms(self, colony_ID: int, torbs: str):
        torb_parsed = self.torb_string_regex(torbs)
        Colony._instances[colony_ID].battle_ready(torb_parsed)
        return
    
    def view_torbs(self, colony_ID, generations = [0,99]):
        if generations == [0, 99]:
            generations = list(range(generations[0], generations[1]))
        if type(generations) == int:
            generations = [generations]
        #Should return string where each line is Torb info from generations
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
        #out_string += "```"
        print(out_string)
        logging.debug(f"{self.log_head()}: Viewing {colony_ID} torbs")
        return out_string

    def call_colony_reproduction(self, colony_ID: int, pairs: str):
        logging.debug(f"{self.log_head()}: Calling colony reproduction in colony {colony_ID}")
        import re
        breeding_list = []
        if pairs == "":
            pairs = "00-01, 00-02"

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
            
            self.colonies[1].colony_reproduction(out_pairs)
            
        logging.info(f"{self.log_head()}: Player requested breeding complete in colony {colony_ID}")
        return
    
    def torb_string_regex(self, torb_str):
        import re
        pattern0 = r"\d{1,2}\s*[-]\s*\d{1,2}"
        pattern1 = r"\d{1,2}"
        
        torb_list = re.findall(pattern0, torb_str)
        out_torb_list = []
        for torb_info in torb_list:
            out_torb_list.append(re.findall(pattern1, torb_info))
        
        return out_torb_list
    
    def find_torb(self, colony_ID, gen: int|str, ID: int|str):
        logging.debug(f"{self.log_head()}: Finding torb {gen}-{ID}")
        sel_colony = None
        out = False
        if type(gen) != list:
            gen = [int(gen)]
        if ID != "any":
            ID = int(ID)
        print(f"gen: {gen}, ID: {ID}")
        out_torbs = []
        for CID, colony in Colony._instances.items():
            print(f"Checking colony {colony.CID} against {colony_ID}")
            if colony.CID == colony_ID:
                print("Found colony")
                sel_colony = colony
                
        
        if sel_colony == None:
            return False
        
        for UID, torb in sel_colony.torbs.items():
            if torb.generation in gen and torb.ID == ID:
                print("Found torb")
                return torb
            elif torb.generation in gen and ID == "any":
                out_torbs.append(torb)
                out = out_torbs
        return out
    
    def log_head(self):
        return f"PID-{self.PID:02d}"