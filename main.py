from torb import *
from colony import *
from gene import *
from player import *
from simulator import *

if __name__ == "__main__":
    S0 = Simulator(0)
    
    EE0 = EvolutionEngine(0)
    print(Colony._instances)
    S0.new_colony("Col0", 0, 0)
    P0 = Player(0)
    #C0 = Colony(0, "C0", 0)
    print(Colony._instances)
    S0.init_all_colonies(8)
    #C0.init_gen_zero(8)
    print(Colony._instances)    
    P0.call_colony_reproduction(0, r"[00-00,/00-01]; 00-02, 00-03 00-04 00-05")
    P0.view_torbs(0, 0)
