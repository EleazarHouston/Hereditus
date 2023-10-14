from exceptions import *
from evolution_engine import EvolutionEngine
import logging
from torb import Torb
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class Colony:
    _instances = {}
    _next_CID = 0
    def __init__(self, CID: int, name: str, EEID: int, PID: int = None):
        self.CID = CID
        self.name = name
        self.EE = EvolutionEngine._instances[EEID]
        #self.PID = PlayerController._instances[PID]
        self.generations = 0
        self.torbs = {}
        self.torb_count = 0
        self.PID = PID
        Colony._instances[self.CID] = self
        Colony._next_CID += 1
        self.at_arms = []
        logging.info(f"{self.log_head()}: Successfully initialized")
        return
    
    def init_gen_zero(self, num_torbs):
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

    def colony_reproduction(self, pairs: list):
        self.generations += 1
        logging.debug(f"{self.log_head()}: Breeding generation {self.generations} with pairs {pairs}")
        for i, pair in enumerate(pairs):
            torb_pair = [self.torbs[pair[0]], self.torbs[pair[1]]]
            child_genes = self.EE.breed_parents(torb_pair)
            if child_genes == False:
                return
            logging.debug(f"{self.log_head()}: Child genes {child_genes} generated")
            child = Torb(i, self.generations, self.CID, parents = torb_pair, genes = child_genes, EEID = self.EE.EEID)
            self.torbs[self.torb_count] = child
            self.torb_count += 1
        logging.info(f"{self.log_head()}: Generation {self.generations} generated")
        return
    
    def log_head(self):
        return f"CID-{self.CID:02d} Colony {self.name:>8}"