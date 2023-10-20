#Describes class Torb
import random
from typing import Any
import numpy as np
import ast
import logging
from exceptions import *
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')
logging.debug("Imported modules")

class Torb:
    _instances = {}
    _next_UID = 0
    def __init__(self, ID: int, generation: int, colony_ID: int = -1, parents: list = [], genes = [], EEID = None):
        from colony import Colony
        from evolution_engine import EvolutionEngine
        self.ID = ID
        self.generation = generation
        self.colony = Colony._instances[colony_ID]
        self.parents = parents
        self.fertile = True
        self.alive = True
        
        #Change to has actual EE, and move initial gene gen to EE
        self.EE = EvolutionEngine._instances[EEID]
        logging.debug(f"{self.log_head()}: Basic attributes set")
        
        self.start_genes(parents, genes)
        self.max_hp = getattr(self,"health").get_allele(is_random=True)
        self.hp = self.max_hp
        self.UID = Torb._next_UID
        Torb._next_UID += 1
        logging.info(f"{self.log_head()}: Successfully instantiated")
        return

    def start_genes(self, parents, genes):
        if not isinstance(parents, list):
            parents = []
        if not isinstance(genes, list):
            genes = []
        if len(genes) != 0:
            self.set_genes(genes, self.EE.EEID)
        if len(parents) == 0 and len(genes) == 0:
            self.random_genes()
        return

    def __str__(self):
        return (f"Colony {self.colony.name}: Torb {self.generation:02d}-{self.ID:02d}")

    def __repr__(self):
        return (f"Torb(ID={self.ID}, generation={self.generation}, colony_ID={self.colony.CID}, parents={self.parents})")

    def get_genes(self):
        genes = [getattr(self, gene) for gene in self.EE.gene_list]
        return genes
    
    def show_genes(self):
        genes = [f"{gene}: {getattr(self, gene).__str__()}" for gene in self.EE.gene_list]
        return genes
    
    def random_genes(self):
        from gene import Gene
        logging.debug(f"Generating random genes for {Torb._next_UID}")
        for i, gene in enumerate(self.EE.gene_list):
            new_gene = Gene(i, [], 0)
            setattr(self, gene, new_gene)
            getattr(self, gene).set_allele(0, is_random=True)
            logging.debug(f"{self.log_head()}: Given genes {getattr(self, gene)}")
        logging.info(f"{self.log_head()}: Successfully given randomized genes")
        return
    
    def set_genes(self, genes, EEID):
        from gene import Gene
        logging.debug(f"{self.log_head()}: Setting genes...")
        for i, gene in enumerate(self.EE.gene_list):
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




#TODO #3 SIMULATOR CLASS






