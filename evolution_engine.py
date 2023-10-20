import logging
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')
from exceptions import *
import random
import numpy as np

#GENE_LIST = ["health", "defense", "agility", "strength"]

class EvolutionEngine:
    _instances = {}
    _next_EID = 0
    def __init__(self,
                 evolution_engine_ID: int,
                 random_gene_min: int = 1,
                 random_gene_max: int = 10,
                 mutation_chance: float = 0.1,
                 mutation_dev: float = 0.15,
                 alleles_per_gene: int = 2,
                 gene_list = ["health", "defense", "agility", "strength"]):
        self.EEID = evolution_engine_ID
        self.gene_min = random_gene_min
        self.gene_max = random_gene_max
        self.mutation_chance = mutation_chance
        self.mutation_dev = mutation_dev
        self.alleles_per_gene = alleles_per_gene
        self.gene_list = gene_list
        EvolutionEngine._instances[self.EEID] = self
        EvolutionEngine._next_EID += 1
        logging.info(f"{self.log_head()}: Successfully initialized")
        return
    
    def verify_parents(self, parents: list):
        from torb import Torb
        logging.debug(f"{self.log_head()}: Verifying parents {parents}")
        if not isinstance(parents[0], Torb) or not isinstance(parents[1], Torb):
            logging.warning(f"{self.log_head()}: Parents {parents} are not valid Torbs")
            raise False
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
            raise InvalidParents(f"{parents} are invalid")
        for parent in parents:
            parent.fertile = False
        genes = []
        for gene in self.gene_list:
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