# DEPRECATED
# THIS IS FROM THE OLD DISCORD VERSION OF THE GAME, BEFORE THE WEB-SERVER VERSION CHANGE

import logging
import random

from player import Player

logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class AIPlayer(Player):
    _AI_instances = {}

    def __init__(self, PID: int = None, name: str = None, AI_type: str = "random"):
        from simulator import Simulator
        self.PID = -len(self._AI_instances)-1 if PID == None else PID
        if name == None:
            name = f"AI{self.PID}"
        super().__init__(PID = PID, name = name)
        self.AI_type = AI_type        
        AIPlayer._AI_instances[self.PID] = (self)
        logging.info(f"{self.log_head()}: Initialization successful")
        
        return

    def create_colonies(self, num_colonies: int):
        logging.debug(f"{self.log_head()}: AI generating Colonies")
        from simulator import Simulator
        from story_strings import AI_names
        from exceptions import SimulatorException
        max_attempts = 10
        
        for i in range(0, num_colonies):
            attempts = 0
            while attempts < max_attempts:
                name = AI_names("random")
                try:
                    Simulator._instances[0].new_colony(name = name, EEID = 0, PID = self.PID)
                    logging.debug(f"{self.log_head()}: New AI Colony created")
                    break
                except SimulatorException as e:

                    attempts += 1
                    if attempts >= max_attempts:
                        logging.error("Max attempts reached for generating unique Colony name")
                        break
                    continue
                
    def make_decisions(self):
        for CID, colony in self.colonies.items():
            logging.debug(f"{self.log_head()}: Decision-making for Colony {colony.name}")
            self.decisions(colony)
        logging.info(f"{self.log_head()}: AI decision-making complete")
        return

    def decisions(self, colony):
        logging.debug(f"{self.log_head()}: AI making decisions in Colony {colony.name}")
        from colony import Colony
        idx = 0
        avail_torbs = [
            torb for ID, torb in colony.torbs.items()
            if torb.alive and torb.fertile and not torb.starving and
            torb not in colony.training and
            torb not in colony.soldiers and
            torb not in colony.growing
        ]
        num_pairs = random.randrange(0, len(colony.torbs)//3)
        desired_enlist = len(colony.torbs)//3
        needed_enlist = desired_enlist - len(colony.soldiers) - len(colony.training)
        num_enlist = random.randrange(0, needed_enlist+1)
        logging.debug(f"{self.log_head()}: Desired enlist {desired_enlist}, needed enlist {needed_enlist}, breed pairs: {num_pairs}")
        random.shuffle(avail_torbs)
        breed_str = ""

        try:
            for i in range(0, num_pairs):
                p1 = f"{avail_torbs[idx].generation}-{avail_torbs[idx].ID}"
                idx += 1
                p2 = f"{avail_torbs[idx].generation}-{avail_torbs[idx].ID}"
                idx += 1
                breed_str += f"{p1}, {p2}, "
            
            logging.debug(f"{self.log_head()}: {colony.name} determined breeding string {breed_str}")
            if breed_str != "":
                self.call_colony_reproduction(colony.CID, breed_str)
            
            enlist_str = ""
            for i in range(0, num_enlist):
                enlist_torb = f"{avail_torbs[idx].generation}-{avail_torbs[idx].ID}, "
                idx += 1
                enlist_str += enlist_torb
            logging.debug(f"{self.log_head()}: {colony.name} determined enlist string {enlist_str}")
            if enlist_str != "":
                self.train_soldiers(colony.CID, enlist_str)

            attack_potential = [colony1 for CID, colony1 in Colony._instances.items()]
            random.shuffle(attack_potential)
            self.set_target(colony.CID, attack_potential[0].name)
            logging.debug(f"{self.log_head()}: Set {colony.name} attack target {colony.attack_target}")
            
        except Exception as e:
            print(e)
            
        finally:
            self.ready_up(colony.CID)
            logging.debug(f"{self.log_head()}: {colony.name} readied up")
        
    def log_head(self) -> str:
        """
        Generates a standard log header for the Player.

        Returns:
            str: Formatted log header string
        """
        
        return f"AI -{self.name[:10]}"