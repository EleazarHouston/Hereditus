from torb import *
from colony import *
from gene import *
from player import *
from simulator import *

if __name__ == "__main__":
    EE0 = EvolutionEngine(0)
    print(Colony._instances)
    C0 = Colony(0, "C0", 0)
    print(Colony._instances)
    C0.init_gen_zero(8)
    print(Colony._instances)
    #print(f"Torbs: {C0.torbs.__str__()}")
    #print(f"Torb0: {C0.torbs[0]}")
    #print(f"Torb0 Genes: {C0.torbs[0].show_genes()}")
    C0.colony_reproduction([[0,1],[2,3],[4,5],[6,7]])
    #print([torb.show_genes() for ID, torb in C0.torbs.items()])
    P1 = Player(0)
    P1.call_colony_reproduction(0, r"[00-00,/00-01]; 00-02, 00-03 00-04 00-05")
    P1.view_torbs(0, 0)
    