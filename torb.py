#Describes class Torb
import random
import numpy as np
import logging
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')
logging.debug("Imported modules")
all_torbs = {}
GENE_LIST = ["health", "defense", "agility", "strength"]

class Torb:
    _instances = {}
    _next_UID = 0
    def __init__(self, ID: int, generation: int, colony_ID: int = -1, parents: list = [], genes = [], EEID = None):
        self.ID = ID
        self.generation = generation
        self.colony = Colony._instances[colony_ID]
        self.parents = parents
        self.fertile = True
        self.alive = True
        logging.debug(f"{self.log_head()}: Basic attributes set")
        if len(parents) == 0 and len(genes) == 0:
            logging.debug(f"{self.log_head()}: Has no parents and no starting genes")
            self.spontaneous_generation = True
            self.random_genes()
        elif len(parents) == 0 and len(genes) != 0:
            logging.warning(f"{self.log_head()}: Has {len(parents)} parents and was given starting genes")
            return
        elif len(parents) != 2:
            logging.warning(f"{self.log_head()}: Has {len(parents)} parents")
            return
        elif len(genes) != 0 and len(parents) == 2:
            self.set_genes(genes, EEID)
        elif parents[0] == parents[1]:
            logging.warning(f"{self.log_head()}: Invalid parents, parent1 = parent2")
            return
        else:
            logging.info(f"{self.log_head()}: Spontaneous generation disabled and not given genes {len(genes)}")
            return
            
        self.max_hp = getattr(self,"health").get_allele(is_random=True)
        self.hp = self.max_hp
        self.UID = Torb._next_UID
        Torb._next_UID += 1
        logging.info(f"{self.log_head()}: Successfully instantiated")
        return

    def __str__(self):
        return (f"Colony {self.colony.name}: Torb {self.generation:02d}-{self.ID:02d}")

    def __repr__(self):
        return (f"Torb(ID={self.ID}, generation={self.generation}, colony_ID={self.colony.CID}, parents={self.parents})")

    def get_genes(self):
        genes = [getattr(self, gene) for gene in GENE_LIST]
        return genes
    
    def show_genes(self):
        genes = [f"{gene}: {getattr(self, gene).__str__()}" for gene in GENE_LIST]
        return genes
    
    def random_genes(self):
        logging.debug(f"Generating random genes for {Torb._next_UID}")
        for i, gene in enumerate(GENE_LIST):
            new_gene = Gene(i, [], 0)
            setattr(self, gene, new_gene)
            getattr(self, gene).set_allele(0, is_random=True)
            logging.debug(f"{self.log_head()}: Given genes {getattr(self, gene)}")
        logging.info(f"{self.log_head()}: Successfully given randomized genes")
        return
    
    def set_genes(self, genes, EEID):
        logging.debug(f"{self.log_head()}: Setting genes...")
        for i, gene in enumerate(GENE_LIST):
            new_gene = Gene(i, genes[i], EEID)
            setattr(self, gene, new_gene)
            logging.debug(f"{self.log_head()}: Got gene {getattr(self, gene)}")
        logging.info(f"{self.log_head()}: Successfully set genes")
        return
    
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
    
    def log_head(self):
        return f"UID-{Torb._next_UID:03d} Colony {self.colony.name:>7}-{self.generation:02d}-{self.ID:02d}"

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
        logging.info(f"{self.log_head()}: Successfully initialized")
        return
    
    def init_gen_zero(self, num_torbs):
        if self.generations != 0:
            logging.warning(f"{self.log_head()}: There are already {self.generations} generations")
            return
        logging.debug(f"{self.log_head()}: Generating generation 0")
        for i in range(num_torbs):
            new_torb = Torb(i, 0, self.CID)
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
            logging.debug(f"{self.log_head()}: Child genes {child_genes} generated")
            child = Torb(i, self.generations, self.CID, parents = torb_pair, genes = child_genes, EEID = self.EE.EEID)
            self.torbs[self.torb_count] = child
            self.torb_count += 1
        logging.info(f"{self.log_head()}: Generation {self.generations} generated")
        return
    #TODO #4 add method to return readable string of all torbs in colony from SQL
    def log_head(self):
        return f"CID-{self.CID:02d} Colony {self.name:>8}"

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
        logging.info(f"{self.log_head()}: Successfully initialized")
        return
    
    def verify_parents(self, parents: list):
        logging.debug(f"{self.log_head()}: Verifying parents {parents}")
        if not isinstance(parents[0], Torb) or not isinstance(parents[1], Torb):
            logging.warning(f"{self.log_head()}: Parents {parents} are not valid Torbs")
            return False
        if parents[0] == parents[1]:
            logging.warning(f"{self.log_head()}: Parents {parents} are the same instance")
            return False
        if any(parent.fertile for parent in parents) == False:
            logging.warning(f"{self.log_head()}: Parents {[parent for parent in parents if parent.fertile == False]} are infertile")
            return False

        #Maybe check if Parent UID found in SQL table    
        logging.info(f"{self.log_head()}: Parents verified")
        return True
    
    def breed_parents(self, parents: list):
        logging.debug(f"{self.log_head()}: Breeding parents {parents}")
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
                if i == 0:
                    alleles.append(random.choice([p0_allele, p1_allele]))
                else:
                    alleles.append(np.mean([p0_allele, p1_allele]))
            alleles = self.mutate_and_shuffle(alleles)
            genes.append(alleles)
            logging.debug(f"{self.log_head()}: Gene {gene} generated {alleles}")
        logging.info(f"{self.log_head()}: Genes generated {genes}")
        return genes
    
    def mutate_and_shuffle(self, alleles):
        logging.debug(f"{self.log_head()}: Mutating and shuffling alleles {alleles}")
        out_alleles = []
        mutated = False
        for allele in alleles:
            die_roll = random.uniform(0, 1)
            if die_roll > 1 - self.mutation_chance:
                allele_hist = allele
                logging.debug(f"{self.log_head()}: Mutation achieved {die_roll} > {1 - self.mutation_chance}")
                mutated = True
                mutation_amount = np.random.normal(0, self.mutation_dev)
                allele = round(allele * (1 + mutation_amount),5)
                logging.info(f"{self.log_head()}: Allele mutated from {allele_hist} to {allele}")
            out_alleles.append(allele)
        random.shuffle(out_alleles)
        logging.info(f"{self.log_head()}: Allele post-mutation box {out_alleles}")
        return out_alleles
    
    def log_head(self):
        return f"EEID-{self.EEID:02d}"

class Gene:
    def __init__(self, GID: int, alleles: list, EEID: int):
        self.GID = GID
        self.alleles = alleles
        self.EE = EvolutionEngine._instances[EEID]
        logging.debug(f"{self.log_head()}: Successfully initialized with alleles {self.alleles}")
        return
    
    def __str__(self):
        return (f"Gene {self.GID}: {self.alleles}")

    def get_allele(self, idx=0, is_random=False):
        if is_random==True:
            out_allele = random.choice(self.alleles)
            return out_allele
        else:
            return self.alleles[idx]
        
    def set_allele(self, start_idx, gene_len: int = None, values=[0], is_random=False):
        logging.debug(f"{self.log_head()}: Setting allele")
        if gene_len == None:
            gene_len = self.EE.alleles_per_gene
            
        if is_random == False:
            self.alleles[start_idx:start_idx+gene_len-1] = values
            logging.debug(f"{self.log_head()}: Alleles set to {values}")
        else:
            alleles = []
            for i in range(0, gene_len):
                alleles.append(random.randrange(self.EE.gene_min,self.EE.gene_max))
            self.alleles[start_idx:start_idx+gene_len-1] = alleles
            logging.debug(f"{self.log_head()}: Alleles set to {alleles}")
        return
    def log_head(self):
        return f"EEID-{self.EE.EEID:02d} {self.EE.gene_list[self.GID]}-gene GID {self.GID:02d}"

EE0 = EvolutionEngine(0)
C0 = Colony(0, "C0", 0)
C0.init_gen_zero(8)
#print(f"Torbs: {C0.torbs.__str__()}")
#print(f"Torb0: {C0.torbs[0]}")
#print(f"Torb0 Genes: {C0.torbs[0].show_genes()}")
C0.colony_reproduction([[0,1],[2,3],[4,5],[6,7]])
#print([torb.show_genes() for ID, torb in C0.torbs.items()])

#torb0 = Torb(0, 0)
#print(torb0)
#print(torb0.show_genes())   
#torb1 = Torb(1, 0)
#torb2 = Torb(2, 1, parents = [0, 1])
#torb3 = Torb(3, 1)


#print(torb2)
#print(torb2.show_genes())
#print(torb2.generation)
