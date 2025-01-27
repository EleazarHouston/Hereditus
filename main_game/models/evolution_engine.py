from django.db import models
import logging
import random
from .game import Game
import numpy as np

logger = logging.getLogger('hereditus')

def default_gene_list():
    return ["vitality", "sturdiness", "agility", "strength"]

# Needed only for past migrations, no longer used
def default_gene_alleles():
    return [5, 5]

class EvolutionEngine(models.Model):
    game = models.OneToOneField(Game, on_delete=models.CASCADE, related_name='evolution_engine_instance')
    random_gene_min =   models.IntegerField(default=1)
    random_gene_max =   models.IntegerField(default=10)
    mutation_chance =   models.FloatField(default=0.1)
    mutation_dev =      models.FloatField(default=0.15)
    alleles_per_gene =  models.IntegerField(default=2)
    gene_list =         models.JSONField(default=default_gene_list)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            logger.info(f"A new EvolutionEngine '{self.pk}' was made for Game {self.game}")
    
    def check_torb_breedable(self, torb):
        if not torb.fertile:
            return False
        return True
    
    def protogenesis_torb(self, colony):
        genes = {}
        for gene in self.gene_list:
            alleles = []
            for i in range(self.alleles_per_gene):
                alleles.append(random.randrange(self.random_gene_min, self.random_gene_max))
            genes[gene] = alleles
        torb = self.new_torb(generation=0, colony=colony, genes=genes)
        
    def __str__(self):
        return f"EvolutionEngine{self.pk} for Game '{self.game.description}'"
    
    def breed_torbs(self, colony, torb0, torb1):
        if not self.check_torb_breedable(torb0) or not self.check_torb_breedable(torb1):
            logger.debug(f"An EvolutionEngine for Colony {colony} in {self.game} tried to breed Torb {torb0.private_ID} '{torb0.name}' and Torb {torb1.private_ID} '{torb1.name}' but one/both weren't breedable")
            return False
        genes = {}
        generation = max(torb0.generation, torb1.generation) + 1
        for gene in self.gene_list:
            alleles = []
            p0_gene = torb0.genes[gene]
            p1_gene = torb1.genes[gene]
            random.shuffle(p0_gene)
            random.shuffle(p1_gene)
            num_alleles = min(len(p0_gene), len(p1_gene))
            
            for i in range(num_alleles):
                # The first allele is a randomly chosen one from the parents
                # subsequent alleles are avg of random alleles from each parent, non-replacing
                if i == 0:
                    alleles.append(max(random.choice([p0_gene[i], p1_gene[i]]),1))
                else:
                    alleles.append(max(round(np.mean([p0_gene[i], p1_gene[i]]),4),1))
            alleles = self.mutate_and_shuffle(alleles)
            genes[gene] = alleles
        logger.debug(f"An EvolutionEngine for Colony {colony} in {self.game} is breeding Torb {torb0.private_ID} '{torb0.name}' and Torb {torb1.private_ID} '{torb1.name}'")
        baby_torb = self.new_torb(generation=generation, colony=colony, genes=genes)
        baby_torb.growing = True
        
        torb0.fertile = torb1.fertile = baby_torb.fertile = False
        torb0.save()
        torb1.save()
        baby_torb.set_action(action="growing")
        #baby_torb.save()
        return baby_torb
    
    def mutate_and_shuffle(self, alleles):
        out_alleles = []
        for allele in alleles:
            die_roll = random.uniform(0, 1)
            if die_roll >= 1 - self.mutation_chance:
                allele_hist = allele # To be used in logging: allele mutated from hist to X
                mutation_amount = np.random.normal(0, self.mutation_dev)
                allele = round(allele * (1 + mutation_amount), 4)
            out_alleles.append(allele)
        random.shuffle(out_alleles)
        return out_alleles
                
                    
    def new_torb(self, generation, colony, genes):
        torb = colony.new_torb(generation=generation, genes=genes)
        logger.debug(f"An EvolutionEngine for Colony {colony} in {self.game} created new Torb {torb.private_ID} '{torb.name}' with Genes {genes}")
        return torb