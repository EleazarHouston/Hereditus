import random

from player import Player

class AIPlayer(Player):
    _AI_instances = {}

    def __init__(self, PID: int = None, name: str = None, AI_type: str = "random"):
        from simulator import Simulator
        self.PID = -len(self._AI_instances)-1 if PID == None else PID
        super().__init__(PID = PID, name = name)
        self.AI_type = AI_type        
        AIPlayer._AI_instances[self.PID] = (self)

    def create_colonies(self, num_colonies: int):
        from simulator import Simulator
        from story_strings import AI_names
        name = AI_names("random")
        for i in range(0, num_colonies):
            Simulator._instances[0].new_colony(name = name, EEID = 0, PID = self.PID)

    def make_decisions(self):
        for CID, colony in self.colonies.items():
            self.decisions(colony)
        return

    def decisions(self, colony):
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
        random.shuffle(avail_torbs)
        breed_str = ""

        try:
            for i in range(0, num_pairs):
                p1 = f"{avail_torbs[idx].generation}-{avail_torbs[idx].ID}"
                idx += 1
                p2 = f"{avail_torbs[idx].generation}-{avail_torbs[idx].ID}"
                idx += 1
                breed_str += f"{p1}, {p2}, "
                
            self.call_colony_reproduction(colony.CID, breed_str)
            enlist_str = ""
            for i in range(0, num_enlist):
                enlist_torb = f"{avail_torbs[idx].generation}-{avail_torbs[idx].ID}, "
                idx += 1
                enlist_str += enlist_torb
            self.train_soldiers(colony.CID, enlist_torb)

            attack_potential = [colony1 for CID, colony1 in Colony._instances.items()]
            random.shuffle(attack_potential)
            self.attack_target(colony.CID, attack_potential[0].name)
            self.ready_up(colony.CID)

        except Exception as e:
            print(e)
        