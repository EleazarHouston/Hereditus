#Describes class Torb
import random
import numpy as np
import logging
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({name}) [{levelname:^8s}] {message}', style='{')
#logging.basicConfig(level=logging.DEBUG)
logging.debug("Imported modules")
all_torbs = {}
# Add to evolution engine later
GENE_LIST = ["health", "defense", "agility", "strength"]

class Torb:
    _instances = {}
    _next_UID = 0
    def __init__(self, ID: int, generation: int, colony_ID: int = -1, parents: list = []):
        self.ID = ID
        self.generation = generation
        self.colony = Colony._instances[colony_ID]
        self.parents = parents
        self.fertile = True
        self.alive = True
        logging.debug(f"UID {Torb._next_UID}-Torb {self.generation:02d}-{self.ID:02d}: basic attributes set")
        if len(parents) == 0:
            logging.debug(f"UID {Torb._next_UID}-Torb {self.generation:02d}-{self.ID:02d} has no parents")
            self.spontaneous_generation = True
            self.random_genes()
        elif len(parents) == 2:
            if parents[0] == parents[1]:
                #Error!
                logging.warning(f"UID {Torb._next_UID}-Torb {self.generation:02d}-{self.ID:02d}: Invalid parents, parent1 = parent2")
                return
        else:
            logging.warning(f"UID{Torb._next_UID}-Torb {self.generation:02d}-{self.ID:02d} has {len(parents)} parents")
            print(f"Must have two parents")
            return
        self.max_hp = getattr(self,"health").get_allele(is_random=True)
        self.hp = self.max_hp
        self.UID = Torb._next_UID
        Torb._next_UID += 1
        logging.info(f"{Torb._next_UID}-Torb {self.generation:02d}-{self.ID:02d} successfully created")
        return

    def __str__(self):
        return (f"Colony {self.colony.name}: Torb {self.generation:02d}-{self.ID:02d}")

    def __repr__(self):
        return (f"Torb(ID={self.ID}, generation={self.generation}, colony_ID={self.colony.CID}, parents={self.parents}")

    def get_genes(self):
        genes = [getattr(self, gene) for gene in GENE_LIST]
        return genes
    
    def show_genes(self):
        #print("Showing genes...")
        genes = [f"{gene}: {getattr(self, gene).__str__()}" for gene in GENE_LIST]
        #print(f"Gene string type: {type(genes[0])}")
        return genes
    
    def random_genes(self):
        logging.debug(f"Generating random genes for {Torb._next_UID}")
        for i, gene in enumerate(GENE_LIST):
            new_gene = Gene(i, [], 0)
            setattr(self, gene, new_gene)
            getattr(self, gene).set_allele(0, is_random=True)
            logging.debug(f"{Torb._next_UID}-Torb {self.generation:02d}-{self.ID:02d} given genes {getattr(self, gene)}")
        logging.info(f"{Torb._next_UID}-Torb {self.generation:02d}-{self.ID:02d} successfully given randomized genes")
        return
    
    def set_genes(self, genes, EEID):
        logging.debug(f"{Torb._next_UID}-Torb {self.generation:02d}-{self.ID:02d}: setting genes...")
        for i, gene in enumerate(GENE_LIST):
            new_gene = Gene(i, genes[i], EEID)
            setattr(self, gene, new_gene)
            logging.debug(f"{Torb._next_UID}-Torb {self.generation:02d}-{self.ID:02d} got gene {getattr(self, gene)}")
        logging.info(f"{Torb._next_UID}-Torb {self.generation:02d}-{self.ID:02d} successfully set genes")
        return

class Colony:
    _instances = {}
    def __init__(self, CID: int, name: str, EEID: int, PID: int = None):
        self.CID = CID
        self.name = name
        self.EE = EvolutionEngine._instances[EEID]
        #self.PID = PlayerController._instances[PID]
        self.generations = 0
        self.torbs = {}
        self.torb_count = 0
        Colony._instances[self.CID] = self
        self.at_arms = []
        return
    
    def init_gen_zero(self, num_torbs):
        if self.generations != 0:
            print("Error")
        for i in range(num_torbs):
            new_torb = Torb(i, 0, self.CID)
            #new_torb.random_genes()
            self.torbs[self.torb_count] = new_torb
            self.torb_count += 1
        return

    def colony_reproduction(self, pairs: list):
        self.generations += 1
        for i, pair in enumerate(pairs):
            torb_pair = [self.torbs[pair[0]], self.torbs[pair[1]]]
            child_genes = self.EE.breed_parents(torb_pair)
            print(f"Child genes: {child_genes}")
            child = Torb(i, self.generations, self.CID, parents = torb_pair)
            child.set_genes(child_genes, self.EE.EEID)
            self.torbs[self.torb_count] = child
            self.torb_count += 1
        return
    #TODO add method to return readable string of all torbs in colony from SQL

#TODO #2 PLAYER CLASS


#TODO #3 SIMULATOR CLASS


class EvolutionEngine:
    _instances = {}

    def __init__(self,
                 evolution_engine_ID: int,
                 random_gene_min: int = 1,
                 random_gene_max: int = 10,
                 mutation_chance: float = 0.1,
                 mutation_dev: float = 0.15,
                 alleles_per_gene: int = 2):
        self.EEID = evolution_engine_ID
        self.gene_min = random_gene_min
        self.gene_max = random_gene_max
        self.mutation_chance = mutation_chance
        self.mutation_dev = mutation_dev
        self.alleles_per_gene = alleles_per_gene
        self.gene_list = GENE_LIST
        EvolutionEngine._instances[self.EEID] = self
        return
    
    def verify_parents(self, parents: list):
        if not isinstance(parents[0], Torb) or not isinstance(parents[1], Torb):
            return False
        if parents[0] == parents[1]:
            return False
        if any(parent.fertile for parent in parents) == False:
            return False
        #is_int = [True for parent in parents if type(parent) == int]
        #all_ints = all(is_int)
        #Check if Parent UID found in SQL table    
        return True

    def generate_alleles(self, parents = []):
        alleles = []
        
        if len(parents) == 0:
            alleles = self.init_all_alleles()
        else:
            self.verify_parents(parents)
            alleles = self.breed_parents(parents)
        return alleles
    
    def breed_parents(self, parents: list):
        if self.verify_parents(parents) == False:
            return
        for parent in parents:
            parent.fertile = False
        genes = []
        for gene in GENE_LIST:
            alleles = []
            for i in range(0, self.alleles_per_gene):
                p0_allele = getattr(parents[0],gene).get_allele(is_random=True)
                p1_allele = getattr(parents[1],gene).get_allele(is_random=True)
                print(f"Parent alleles: {p0_allele}, {p1_allele}")
                if i == 0:
                    alleles.append(random.choice([p0_allele, p1_allele]))
                else:
                    alleles.append(np.mean([p0_allele, p1_allele]))
            print(f"Pre-mutate alleles: {alleles}")
            alleles = self.mutate_and_shuffle(alleles)
            print(f"Shuffled: {alleles}")
            genes.append(alleles)
        print(f"Out genes: {genes}")
        return genes
    
    def mutate_and_shuffle(self, alleles):
        out_alleles = []
        mutated = False
        for allele in alleles:
            die_roll = random.uniform(0, 1)
            if die_roll > 1 - self.mutation_chance:
                mutated = True
                mutation_amount = np.random.normal(0, self.mutation_dev)
                allele = round(allele * (1 + mutation_amount),5)
                print(f"Mutated: {allele}")
            out_alleles.append(allele)
        print(f"Mutated alleles: {out_alleles}")
        random.shuffle(out_alleles)
        return out_alleles
    
    def lower_hp(self, amount):
        hp = max(self.hp - amount, 0)
        if self.hp == 0:
            #Maybe create separate death method later
            self.alive = False
            self.fertile = False
        return

    def raise_hp(self, amount):
        #Maybe combine into one adjust hp method
        hp = min(self.hp + amount, self.max_hp)
        return

class Gene:
    def __init__(self, GID: int, alleles: list, EEID: int):
        self.GID = GID
        self.alleles = alleles
        self.EE = EvolutionEngine._instances[EEID]
        return
    
    def __str__(self):
        return (f"Gene {self.GID}: {self.alleles}")

    def get_allele(self, idx=0, is_random=False):
        if is_random==True:
            return random.choice(self.alleles)
        else:
            return self.alleles[idx]
    def set_allele(self, start_idx, gene_len: int = None, values=[0], is_random=False):
        #print("Setting allele...")
        if gene_len == None:
            gene_len = self.EE.alleles_per_gene
            
        if is_random == False:
            self.alleles[start_idx:start_idx+gene_len-1] = values
        else:
            alleles = []
            #print(f"len: {gene_len}")
            for i in range(0, gene_len):
                alleles.append(random.randrange(self.EE.gene_min,self.EE.gene_max))
            self.alleles[start_idx:start_idx+gene_len-1] = alleles
            #print(self.alleles)
        return

EE0 = EvolutionEngine(0)
C0 = Colony(0, "C0", 0)
C0.init_gen_zero(8)
#print(f"Torbs: {C0.torbs.__str__()}")
#print(f"Torb0: {C0.torbs[0]}")
print(f"Torb0 Genes: {C0.torbs[0].show_genes()}")
C0.colony_reproduction([[0,1],[2,3],[4,5],[6,7]])
print([torb.show_genes() for ID, torb in C0.torbs.items()])

#torb0 = Torb(0, 0)
#print(torb0)
#print(torb0.show_genes())   
#torb1 = Torb(1, 0)
#torb2 = Torb(2, 1, parents = [0, 1])
#torb3 = Torb(3, 1)


#print(torb2)
#print(torb2.show_genes())
#print(torb2.generation)
