from __future__ import annotations

import logging
import random

import numpy as np

from exceptions import EvolutionEngineException, InvalidParents
from torb import Torb
from gene import Gene


logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class EvolutionEngine:
    """
    Handles the genetics of the Torbs (and Colonies).

    Attributes:
        EEID (int): Unique EvolutionEngine ID
        gene_min (int): The minimum value when randomly generating alleles
        gene_max (int): The maximum value when randomly generating alleles
        mutation_chance (float): The chance that an allele will randomly mutate
        mutation_dev (float): The standard deviation from the initial value an allele can mutate
        alleles_per_gene (int): The number of alleles that will comprise each Gene
        gene_list (list[str]): A list of the names of the types of Genes each Torb will have
        mutated (bool): Denotes whether or not the gene has mutated
        
    Class Attributes:
        _instances (dict[int, EvolutionEngine]): Stores all EvolutionEngine instances with their EEID as keys
        _next_EEID (int): The next available EEID
    """
    
    _instances: dict[int, EvolutionEngine] = {}
    _next_EEID: int = 0
    
    def __init__(self,
                 evolution_engine_ID: int,
                 random_gene_min: int = 1,
                 random_gene_max: int = 10,
                 mutation_chance: float = 0.1,
                 mutation_dev: float = 0.15,
                 alleles_per_gene: int = 2,
                 gene_list: list[str] = ["health", "defense", "agility", "strength"]):
        """
        Initializes a new EvolutionEngine instance.

        Args:
            evolution_engine_ID (int): Unique EvolutionEngine ID
            random_gene_min (int, optional): The minimum value a randomly generated allele can be, defaults to 1
            random_gene_max (int, optional): The maximum value a randomly generated allele can be, defaults to 10
            mutation_chance (float, optional): The chance that a random mutation will occur, defaults to 0.1
            mutation_dev (float, optional): The standard deviation multiplayer when an allele mutates, defaults to 0.15
            alleles_per_gene (int, optional): Number of alleles to generate per Gene, defaults to 2
            gene_list (list[str], optional): List of Gene names each Torb will have, defaults to ["health", "defense", "agility", "strength"].
        """
        
        self.EEID: int = evolution_engine_ID
        self.gene_min: int = random_gene_min
        self.gene_max: int = random_gene_max
        self.mutation_chance: float = mutation_chance
        self.mutation_dev: float = mutation_dev
        self.alleles_per_gene: int = alleles_per_gene
        self.gene_list: list[str] = gene_list
        EvolutionEngine._instances[self.EEID] = self
        EvolutionEngine._next_EEID += 1
        logging.info(f"{self.log_head()}: Successfully initialized")
        return
    
    def verify_parents(self, parents: list[Torb]) -> bool:
        """
        Determines if given Torbs are valid parents.

        Args:
            parents (list[Torb]): List of two Torbs to check if valid parents

        Returns:
            bool: Whether or not parents are valid
        """
        
        if len(parents) != 2:
            raise EvolutionEngineException(f"{self.log_head()}: Invalid number of parents given: {len(parents)}")
        logging.debug(f"{self.log_head()}: Verifying parents {parents}")
        if not isinstance(parents[0], Torb) or not isinstance(parents[1], Torb):
            raise EvolutionEngineException(f"{self.log_head()}: Parents {parents} are not valid Torbs")
        if parents[0] == parents[1]:
            raise EvolutionEngineException(f"{self.log_head()}: Parents {parents} are the same instance")
        if any(parent.fertile for parent in parents) == False:
            raise EvolutionEngineException(f"{self.log_head()}: Parents {[parent for parent in parents if parent.fertile == False]} are infertile")
 
        logging.info(f"{self.log_head()}: Parents verified")
        return True
    
    def breed_parents(self, parents: list[Torb]) -> list[Gene]:
        """
        Breeds parents together and returns genes for child Torb.

        Args:
            parents (list[Torb]): List of two Torbs to breed together

        Returns:
            list[Gene]: A list of Genes for the child Torb
        """
        
        logging.debug(f"{self.log_head()}: Breeding parents {parents}")
        if self.verify_parents(parents) == False:
            raise InvalidParents(f"{parents} are invalid")
        for parent in parents:
            print(f"Setting {parent.colony.name} {parent.generation}-{parent.ID} infertile")
            parent.fertile = False
        genes = []
        for j, gene in enumerate(self.gene_list):
            alleles = []
            for i in range(0, self.alleles_per_gene):
                p0_allele = getattr(parents[0],gene).get_allele(is_random=True)
                p1_allele = getattr(parents[1],gene).get_allele(is_random=True)
                if i == 0:
                    alleles.append(random.choice([p0_allele, p1_allele]))
                else:
                    alleles.append(np.mean([p0_allele, p1_allele]))
            alleles, mutated = self.mutate_and_shuffle(alleles)
            genes.append(Gene(j, alleles, self.EEID))
            genes[-1].mutated = True if mutated == True else genes[-1].mutated
            logging.debug(f"{self.log_head()}: Gene {gene} generated {alleles}")
        logging.info(f"{self.log_head()}: Genes generated {genes}")
        return genes
    
    def mutate_and_shuffle(self, alleles: list[float]) -> list[float]:
        """
        Mutates and randomly shuffles alleles

        Args:
            alleles (list[float]): A list of input alleles to mutate and shuffle

        Returns:
            list[float]: A list of alleles as floats
        """
        mutated = False
        logging.debug(f"{self.log_head()}: Mutating and shuffling alleles {alleles}")
        out_alleles = []
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
        return out_alleles, mutated
    
    def create_torb(self, ID: int, generation: int, CID: int, parents: list[Torb]=[], genes: list[Gene]=None):
        logging.info(f"{self.log_head()}: Calling creation of Torb {generation:02d}-{ID:02d}")
        if parents:
            genes = self.breed_parents(parents)
        torb = Torb(ID, generation, CID, parents, genes, EEID = self.EEID)
        return torb
    
    def inbred_factor(self, torb):
        
        if torb.inbred < 0.01:
            return
        factor = (1/(torb.inbred+1))**0.5
        for gene_type in self.gene_list:
            gene = getattr(torb, gene_type)
            new_alleles = []
            for allele in gene.alleles:
                new_alleles.append(allele * factor)
            gene.alleles = new_alleles
        return factor

    def adjust_gene(self, torb: Torb, amount: int, is_random: bool = True):
        if is_random == True:
            sel_gene_type = random.choice(self.gene_list)
            sel_gene = getattr(torb, sel_gene_type)
            cur_alleles = sel_gene.alleles
            sel_allele_idx = random.randrange(0, self.alleles_per_gene-1)
            cur_alleles[sel_allele_idx] += amount
            sel_gene.alleles = cur_alleles
        else:
            raise EvolutionEngineException("Not implemented yet")
        return

    def log_head(self):
        return f"EEID-{self.EEID:02d}"