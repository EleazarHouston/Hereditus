

class Simulator:
    def __init__(self, SID):
        self.SID = SID
        self.colonies = {}
        self.colony_count = 0
        return
    
    def new_colony(self, name, EEID, PID):
        from colony import Colony
        self.colonies[Colony._next_CID] = Colony(Colony._next_CID, name, EEID, PID)
        self.colony_count += 1
        return
    
    def init_all_colonies(self, num_torbs):
        for CID, colony in self.colonies.items():
            colony.init_gen_zero(num_torbs)
        return
    
    def battle(self, army0: list, army1: list):
        for c0_torb, c1_torb in army0, army1:
            print(f"C0: {c0_torb.UID}")
            print(f"C1: {c1_torb.UID}")
        return
    
    def next_round(self):
        return
        