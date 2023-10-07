#Describes class Torb
import random


all_torbs = {}
GENE_LIST = ["health", "defense", "agility", "strength"]
num_alleles_per_gene = 2

gene_min = 1
gene_max = 10

class Torb:
    def __init__(self, ID: int, generation: int, colony_ID: int = -1, parents = []):
        self.ID = ID
        self.generation = generation
        self.colony_ID = colony_ID

        if len(parents) == 0:
            self.spontaneous_generation = True
        elif len(parents) == 2:
            if parents[0] == parents[1]:
                #Error!
                print(f"Hey you can't do that. {parents[0]} = {parents[1]}")
                return


        return

    def __str__(self):
        return (f"Colony_ID: {self.colony_ID:02d}: Torb {self.generation:02d}-{self.ID:02d}")

    def get_genes(self, int):
        print(f"This is where the genes will go: {int}")
        return
    def call_add_one(self, int):
        return add_one(int)
        

def add_one(int):
    return int+1


torb1 = Torb(2, 1, parents = [0, 1])
torb2 = Torb(3, 1)

print(torb1)
torb1.get_genes(7)
print(torb1.generation)

#Gen 0, ID 1
#Colony StarWars: Entity 00-01
#Colony StarWars: Entity 10-12


#TODO #1 COLONY CLASS


#TODO #2 PLAYER CLASS


#TODO #3 SIMULATOR CLASS


class EvolutionEngine:
    def __init__(self,
                 evolution_engine_ID: int,
                 random_gene_min: int = 1,
                 random_gene_max = 10,
                 mutation_chance: float = 0.1,
                 alleles_per_gene: int = 2):
        self.EID = evolution_engine_ID
        self.gene_min = random_gene_min
        self.gene_max = random.gene_max
        self.mutation_chance = mutation_chance
        return
    
    def verify_parents(self, parents: list):
        x = 1
        #is_int = [True for parent in parents if type(parent) == int]
        #all_ints = all(is_int)
        #Check if Parent UID found in SQL table    
        return

    def generate_alleles(self, parents = []):
        alleles = []
        
        if len(parents) == 0:
            alleles = self.init_all_alleles()
        else:
            self.verify_parents(parents)
            alleles = self.breed_parents(parents)
        return alleles
    
    def breed_parents(self, parents: list):
        #Add SQL connection here
        
        for gene in GENE_LIST:
            #Get parents genes.
            x = 1
        return
    
    def init_all_alleles(self):
        return 0
    
    def random_allele(self):
        allele = random.randrange(self.gene_min, self.gene_max)
        return
    
#Test