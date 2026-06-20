import random

from django.db import models

from .game import Game


def default_gene_list():
    return ["vitality", "sturdiness", "agility", "strength", "intelligence"]


def default_gene_alleles():
    return [5, 5]


class EvolutionEngine(models.Model):
    game = models.OneToOneField(
        Game,
        on_delete=models.CASCADE,
        related_name="evolution_engine_instance",
    )
    random_gene_min = models.IntegerField(default=1)
    random_gene_max = models.IntegerField(default=10)
    mutation_chance = models.FloatField(default=0.1)
    mutation_dev = models.FloatField(default=0.15)
    alleles_per_gene = models.IntegerField(default=2)
    gene_list = models.JSONField(default=default_gene_list)

    def check_torb_breedable(self, torb):
        return torb.fertile and torb.is_alive and not torb.growing

    def protogenesis_torb(self, colony, rng=None):
        rng = rng or random.Random()
        genes = {}
        for gene in self.gene_list:
            while True:
                alleles = [
                    rng.randrange(self.random_gene_min, self.random_gene_max)
                    for _ in range(self.alleles_per_gene)
                ]
                if any(allele > self.random_gene_max / 2 for allele in alleles):
                    break
            genes[gene] = alleles
        return self.new_torb(generation=0, colony=colony, genes=genes, rng=rng)

    def breed_torbs(self, colony, torb0, torb1, rng=None):
        rng = rng or random.Random()
        if not self.check_torb_breedable(torb0) or not self.check_torb_breedable(torb1):
            return False
        genes = {}
        generation = max(torb0.generation, torb1.generation) + 1
        for gene in self.gene_list:
            parent0 = list(torb0.genes[gene])
            parent1 = list(torb1.genes[gene])
            rng.shuffle(parent0)
            rng.shuffle(parent1)
            alleles = []
            for index in range(min(self.alleles_per_gene, len(parent0), len(parent1))):
                if index == 0:
                    allele = rng.choice([parent0[index], parent1[index]])
                else:
                    allele = round((parent0[index] + parent1[index]) / 2, 4)
                alleles.append(max(allele, 1))
            genes[gene] = self.mutate_and_shuffle(alleles, rng=rng)
        baby = self.new_torb(generation=generation, colony=colony, genes=genes, rng=rng)
        baby.growing = True
        torb0.fertile = False
        torb1.fertile = False
        baby.fertile = False
        torb0.save(update_fields=["fertile"])
        torb1.save(update_fields=["fertile"])
        baby.set_action(action="growing")
        return baby

    def mutate_and_shuffle(self, alleles, rng=None):
        rng = rng or random.Random()
        result = []
        for allele in alleles:
            if rng.random() >= 1 - self.mutation_chance:
                allele = round(allele * (1 + rng.gauss(0, self.mutation_dev)), 4)
            result.append(max(allele, 1))
        rng.shuffle(result)
        return result

    def new_torb(self, generation, colony, genes, rng=None):
        return colony.new_torb(generation=generation, genes=genes, rng=rng)

    def __str__(self):
        return f"EvolutionEngine{self.pk} for Game '{self.game.description}'"
