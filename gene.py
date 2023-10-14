import random
import logging
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class Gene:
    def __init__(self, GID: int, alleles: list, EEID: int):
        from evolution_engine import EvolutionEngine
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