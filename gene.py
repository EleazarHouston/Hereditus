import random
import logging
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class Gene:
    """
    Represents a Gene in a given Torb.
    
    Attributes:
        GID (int): Unique Gene ID
        alleles (list): List of integers representing Gene alleles
        EE (EvolutionEngine): The EvolutionEngine assigned to the Gene
    """
    
    def __init__(self, GID: int, alleles: list, EEID: int) -> None:
        """
        Initializes a new Gene instance.

        Args:
            GID (int): Unique Gene ID
            alleles (list): List of alleles
            EEID (int): The ID of the Evolution Engine assigned to the Gene
        """
        
        from evolution_engine import EvolutionEngine
        self.GID = GID
        self.alleles = alleles
        self.EE = EvolutionEngine._instances[EEID]
        logging.debug(f"{self.log_head()}: Successfully initialized with alleles {self.alleles}")
        return
    
    def __str__(self) -> str:
        return (f"Gene {self.GID}: {self.alleles}")

    def get_allele(self, idx=0, is_random=False) -> int:
        """
        Returns requested allele value.

        Args:
            idx (int, optional): Allele index desired, defaults to 0.
            is_random (bool, optional): Whether to return a random allele or not, defaults to False.

        Returns:
            int: Value of allele
        """
        if is_random==True:
            out_allele = random.choice(self.alleles)
            return out_allele
        else:
            return self.alleles[idx]
        
    def set_allele(self, start_idx: int, gene_len: int = None, values: list = [0], is_random: bool = False) -> None:
        """
        Sets allele(s) of Gene at certain index.

        Args:
            start_idx (_type_): _description_
            gene_len (int, optional): _description_. Defaults to None.
            values (list, optional): _description_. Defaults to [0].
            is_random (bool, optional): _description_. Defaults to False.
        """
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
    
    def log_head(self) -> None:
        """
        Generates a standard log header for the Gene.

        Returns:
            str: Formatted log header string
        """
        return f"EEID-{self.EE.EEID:02d} {self.EE.gene_list[self.GID]}-gene GID {self.GID:02d}"