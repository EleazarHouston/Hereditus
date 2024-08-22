from __future__ import annotations
import logging

from gene import Gene

logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class Torb:
    """
    Represents the primary creature managed and bred in the game.

    Attributes:
        ID (int): The player-facing ID (per Colony, per generation)
        UID (int): The Unique Torb ID across the entire game
        generation (int): The generation number the Torb is in
        colony (Colony): The Colony the Torb is a part of
        parents (list[Torb]): A list of the two parents of the Torb, or empty if no parents
        fertile (bool): Represents whether Torb can breed or not
        alive (bool): Represents whether the Torb is alive or not
        EE (EvolutionEngine): The EvolutionEngine assigned to handle the Torb's genetics
        hp (int): Current hit points
        max_hp (int): The maximum number of hit points the Torb can have
        health (Gene): The Gene associated with the Torb's health
        defense (Gene): The Gene associated with the Torb's defense
        agility (Gene): The Gene associated with the Torb's agility
        strength (Gene): The Gene associated with the Torb's strength
    
    CLass Attributes:
        _instances (dict[int, Torb]): Stores all Torb instances with their UID as keys
        _next_UID (int): The next available UID
    """
    
    _instances: dict[int, Torb] = {}
    _next_UID: int = 0
    
    def __init__(self, ID: int, generation: int, colony_ID: int = -1, parents: list[Torb] = [], genes: list[Gene] = [], EEID: int = None):
        """
        Initializes a new Torb instance.

        Args:
            ID (int): Colony & generation specific local ID for the Torb
            generation (int): The generation the Torb is a part of
            colony_ID (int, optional): ID of the Colony the Torb lives in. defaults to -1
            parents (list, optional): List of Torb's parents, defaults to []
            genes (list, optional): List of Torb's Genes, defaults to []
            EEID (int, optional): ID for EvolutionEngine assigned to Torb's genetics, defaults to None
        """
        
        from colony import Colony
        from evolution_engine import EvolutionEngine
        self.ID = ID
        self.generation = generation
        self.colony = Colony._instances[colony_ID]
        self.parents = parents
        self.fertile = True
        self.alive = True
        self.starving = False
        self.poisoned = False
        self.inbred = 0.0
        self.ancestry = []
        self.mutagen_resistance = 1
        self.EE = EvolutionEngine._instances[EEID]
        logging.debug(f"{self.log_head()}: Basic attributes set")
        
        self.start_genes(parents, genes)
        self.max_hp = round(getattr(self,"health").get_allele(is_random=True))
        self.hp = self.max_hp
        
        if len(self.parents) == 2:
            logging.debug(f"{self.log_head()}: Setting ancestry and determining inbred value")
            self.init_ancestry()
            self.inbred = self.det_inbred()
        
        self.UID = Torb._next_UID
        logging.info(f"{self.log_head()}: Successfully instantiated")
        Torb._next_UID += 1
        return

    def start_genes(self, parents, genes):
        # Move initial gene gen to EE
        if not isinstance(parents, list):
            parents = []
        if not isinstance(genes, list):
            genes = []
        if len(genes) != 0:
            self.set_genes(genes, self.EE.EEID)
        if len(parents) == 0 and len(genes) == 0:
            self.random_genes()
        return

    def init_ancestry(self, generations: int = 4):
        if len(self.parents) != 2:
            return
        
        gen_size = 2
        parent0 = self.parents[0]
        parent1 = self.parents[1]
        ancestry = [parent0, parent1]

        for i in range(generations):
            logging.debug(f"{self.log_head()}: Checking Torb ancestor gen {i}")
            if i * gen_size < len(parent0.ancestry):
                logging.debug(f"{self.log_head()}: Parent0 ancestry {parent0.ancestry}")
                p0_ancestors = parent0.ancestry[i*gen_size:(i+1)*gen_size]
            else:
                p0_ancestors = []
            if i * gen_size < len(parent1.ancestry):
                logging.debug(f"{self.log_head()}: Parent1 ancestry {parent1.ancestry}")
                p1_ancestors = parent1.ancestry[i*gen_size:(i+1)*gen_size]
            else:
                p1_ancestors = []
            
            ancestry.extend(p0_ancestors + p1_ancestors)
            gen_size *= 2
        self.ancestors = ancestry
        logging.debug(f"{self.log_head()}: Ancestry set to {ancestry}")
        return

    def det_inbred(self):
        import math
        weight = 0
        inbred = 0.25 * math.floor((self.parents[0].inbred + self.parents[1].inbred)*4)/4
        logging.debug(f"{self.log_head()}: Parent inbred factor {inbred}")
        for i, ancestor in enumerate(self.ancestry):
            if ancestor in self.ancestry[:i]:
                
                found_gen = int(math.log2((i+2)/2))
                weight = 1/found_gen
                inbred += weight
                logging.debug(f"{self.log_head()}: Ancestor found gen {found_gen} weight {weight}")
        
        logging.debug(f"{self.log_head()}: Inbred total {inbred}")
        return inbred

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
        logging.critical(f"DEPRECATED RANDOM_GENE INIT METHOD")
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
        if all(isinstance(gene, Gene) for gene in genes):
            for i, gene_name in enumerate(self.EE.gene_list):
                setattr(self, gene_name, genes[i])
                logging.debug(f"{self.log_head()}: Got gene {getattr(self, gene_name)}")
        else:
            logging.error("Provided genes are not instances of Gene class.")
        logging.info(f"{self.log_head()}: Successfully set genes")
        return
    
    def lower_hp(self, amount):
        # DEPRECATED
        logging.warning(f"{self.log_head()}: Deprecated function 'lower_hp'")
        self.hp = max(self.hp - amount, 0)
        if self.hp == 0:
            #Maybe create separate death method later
            self.alive = False
            self.fertile = False
        return

    def raise_hp(self, amount):
        # DEPRECATED
        logging.warning(f"{self.log_head()}: Deprecated function 'raise_hp'")
        self.hp = min(self.hp + amount, self.max_hp)
        return
    
    def adjust_hp(self, amount: int) -> None:
        """
        Adjust the HP of the Torb by a given amount.

        Args:
            amount (int): Positive values increase HP, negative values decrease HP.
        """
        self.hp = min(max(self.hp + amount, 0), self.max_hp)
        if self.hp == 0:
            self.alive = False
            self.fertile = False
        return
    
    def log_head(self):
        return f"UID-{Torb._next_UID:03d} Colony {self.colony.name:>7}-{self.generation:02d}-{self.ID:02d}"
