from colony import Colony
from exceptions import *
from evolution_engine import EvolutionEngine
import logging
from torb import Torb
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class Player:
    _instances = {}
    def __init__(self, PID):
        self.PID = PID
        self.colonies = {}
        self.colony_count = 0
        Player._instances[PID] = self
        return
    
    def assign_colony(self, CID):
        if CID in Colony._instances:
            Colony._instances[CID].PID = self.PID
            self.colonies[self.colony_count+1]=(Colony._instances[CID])
            self.colony_count += 1
        else:
            raise PlayerException("Cannot claim nonexistant colony")
        return
    
    
    
    def view_torbs(self, colony_ID, generations = [0,99]):
        from unittest.mock import ANY
        if type(generations) == list:
            generations = range(generations[0], generations[1])
        #Should return string where each line is Torb info from generations
        found_torbs = self.find_torb(colony_ID, generations, "any")
        out_string = ""
        for torb in found_torbs:
            out_string += f"\nColony {torb.colony.name} Torb {torb.generation:02d}-{torb.ID:02d}: {torb.hp}/{torb.max_hp} hp"
        print(out_string)
        return

    def call_colony_reproduction(self, colony_ID: int, pairs: str):
        import re
        breeding_list = []
        if pairs == "":
            pairs = "00-01, 00-02"
        
        pattern1 = r"\d{1,2}\s*[-]\s*\d{1,2}"
        breeding_list = re.findall(pattern1, pairs)
        print(f"List1: {breeding_list}")
        pattern2 = r"\d{1,2}"
        breeding_torbs_info = []
        for torb_info in breeding_list:
            print(f"Splitting {torb_info}")
            breeding_torbs_info.append(re.findall(pattern2, torb_info))
        print(breeding_list)
        print(breeding_torbs_info)
        
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

        return
    
    def find_torb(self, colony_ID, gen: int|str, ID: int|str):
        out = False
        if type(gen) != list:
            gen = [int(gen)]
        if ID != "any":
            ID = int(ID)
        print(f"gen: {gen}, ID: {ID}")
        out_torbs = []
        for CID, colony in Colony._instances.items():
            for UID, torb in colony.torbs.items():
                if torb.generation in gen and torb.ID == ID:
                    print("Found torb")
                    return torb
                elif torb.generation in gen and ID == "any":
                    out_torbs.append(torb)
                    out = out_torbs
        print("Not found")
        return out