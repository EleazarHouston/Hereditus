from __future__ import annotations
from dataclasses import dataclass
import random

@dataclass
class Discovery:
    DID: int
    prereqs: list[Discovery]
    title: str
    desc: str = ""
    cost: int = 1

class ResearchTree:
    # D0# = Thinking
    D00 = Discovery(0, [], "Thinking")
    D01 = Discovery(1, [D00], "Advanced Thinking", cost = 3)
    D02 = Discovery(2, [D01], "Scientific Thinking", cost = 5)
    D03 = Discovery(3, [D02], "Revolutionary Thinking", cost = 16)
    
    # D1# = Building
    D10 = Discovery(11, [D00], "Buildings")
    D11 = Discovery(12, [D10, D01], "Walls") # Increase defenses
    D12 = Discovery(13, [D02, D10], "Hospitals")
    D13 = Discovery(14, [D10], "Granary")
    D14 = Discovery(15, [D10], "Dormitories")
            
    # D2# = General Research
    D20 = Discovery(20, [D01], "Stealth") # Hides army info
    D21 = Discovery(21, [D01, D10], "Trade")
    D22 = Discovery(22, [D01, D10], "Metal")
    D23 = Discovery(23, [D01], "Farming") # Invest Food for return

    
    # D3# = Specialties
    D30 = Discovery(30, [D20], "Theft")
    D31 = Discovery(31, [D02, D20], "Poison") # Bait food
    D32 = Discovery(32, [D22], "Advanced Soldier")
    
    # D4# = Genetics
    D40 = Discovery(40, [D02], "Mutagen", cost = 5)
    D41 = Discovery(41, [D02, D40], "Gene Shuffle", cost=10)
    D42 = Discovery(42, [D41], "Gene Randomization", cost=20)
    D43 = Discovery(43, [D03, D42], "Gene Reset", cost = 30)
    D44 = Discovery(44, [D43], "Gene Reset II", cost =40)
    D49 = Discovery(49, [D03, D43], "Gene Maximization", cost = 75)

    tree = [D00, D01, D02, D03,
            D10, D11, D12, D13, D14,
            D20, D21, D22,
            D30, D31,
            D40, D41, D42, D43, D44, D49]

    def __init__(self):
        self.tree = ResearchTree.tree # All discoveries in the simulation
        self.researched = []
        self.available = [ResearchTree.D00]
    
    def discover(self, points):
        if len(self.available) == 0:
            return None, "No Discoveries available"
        random.shuffle(self.available)
        for discovery in self.available:
            if points >= discovery.cost:
                self.researched.append(discovery)
                self.available.remove(discovery)
                self.check_available()
                return discovery.title, discovery.desc, discovery.cost
        return None, "Not enough points for available Discoveries"

    def check_available(self):
        for discovery in self.tree:
            if all(discovery.prereqs) in self.researched:
                self.available.append(discovery)
        if len(self.available) == 0 and len(self.researched) == 0:
            self.available.append(ResearchTree.D00)
        return len(self.available)