

class Simulator:
    def __init__(self, SID):
        self.SID = SID
        return
    
    
    def new_colony(self, name, EEID, PID):
        from colony import Colony
        self.colonies[self.colony_count+1] = Colony(Colony._next_CID, name, EEID, self.PID)
        self.colony_count += 1
        return