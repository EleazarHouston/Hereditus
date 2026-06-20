import copy
import random

from django.test import TestCase

from main_game.tests.factories import ColonyFactory, TorbFactory


class PredictableRng:
    def __init__(self, *, random_value=0.0, gauss_value=0.0):
        self.random_value = random_value
        self.gauss_value = gauss_value
        self.gauss_calls = []

    def shuffle(self, values):
        return None

    def choice(self, values):
        return values[0]

    def random(self):
        return self.random_value

    def gauss(self, mean, deviation):
        self.gauss_calls.append((mean, deviation))
        return self.gauss_value


class GeneticsTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory()
        self.engine = self.colony.game.evolution_engine_instance

    def test_protogenesis_respects_gene_and_allele_configuration(self):
        self.engine.gene_list = ["vitality", "strength", "intelligence"]
        self.engine.alleles_per_gene = 3
        self.engine.random_gene_min = 2
        self.engine.random_gene_max = 8

        torb = self.engine.protogenesis_torb(self.colony, rng=random.Random(7))

        self.assertEqual(set(torb.genes), set(self.engine.gene_list))
        for alleles in torb.genes.values():
            self.assertEqual(len(alleles), 3)
            self.assertTrue(all(2 <= allele < 8 for allele in alleles))
            self.assertTrue(any(allele > 4 for allele in alleles))

    def test_breeding_inherits_alleles_without_mutating_parents(self):
        self.engine.gene_list = ["vitality"]
        self.engine.mutation_chance = 0
        first = TorbFactory(
            colony=self.colony,
            private_ID=1,
            generation=2,
            genes={"vitality": [8, 4]},
            hp=8,
            max_hp=8,
        )
        second = TorbFactory(
            colony=self.colony,
            private_ID=2,
            generation=3,
            genes={"vitality": [6, 2]},
            hp=6,
            max_hp=6,
        )
        first_genes = copy.deepcopy(first.genes)
        second_genes = copy.deepcopy(second.genes)

        baby = self.engine.breed_torbs(
            self.colony,
            first,
            second,
            rng=PredictableRng(),
        )

        self.assertEqual(baby.genes["vitality"], [8, 3.0])
        self.assertEqual(baby.generation, 4)
        self.assertEqual(first.genes, first_genes)
        self.assertEqual(second.genes, second_genes)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.genes, first_genes)
        self.assertEqual(second.genes, second_genes)

    def test_breeding_caps_alleles_at_engine_limit(self):
        self.engine.gene_list = ["vitality"]
        self.engine.alleles_per_gene = 2
        self.engine.mutation_chance = 0
        first = TorbFactory(
            colony=self.colony,
            private_ID=1,
            genes={"vitality": [8, 6, 4]},
            hp=8,
            max_hp=8,
        )
        second = TorbFactory(
            colony=self.colony,
            private_ID=2,
            genes={"vitality": [7, 5, 3]},
            hp=7,
            max_hp=7,
        )

        baby = self.engine.breed_torbs(
            self.colony,
            first,
            second,
            rng=PredictableRng(),
        )

        self.assertEqual(len(baby.genes["vitality"]), 2)

    def test_mutation_chance_zero_preserves_alleles(self):
        self.engine.mutation_chance = 0

        result = self.engine.mutate_and_shuffle([2, 5], rng=PredictableRng())

        self.assertEqual(result, [2, 5])

    def test_mutation_chance_one_uses_configured_deviation_and_floor(self):
        self.engine.mutation_chance = 1
        self.engine.mutation_dev = 0.25
        rng = PredictableRng(random_value=0, gauss_value=-2)

        result = self.engine.mutate_and_shuffle([4, 2], rng=rng)

        self.assertEqual(result, [1, 1])
        self.assertEqual(rng.gauss_calls, [(0, 0.25), (0, 0.25)])

    def test_unbreedable_parent_prevents_birth(self):
        first = TorbFactory(colony=self.colony, private_ID=1, fertile=False)
        second = TorbFactory(colony=self.colony, private_ID=2)
        count = self.colony.torbs.count()

        result = self.engine.breed_torbs(self.colony, first, second, rng=random.Random(0))

        self.assertFalse(result)
        self.assertEqual(self.colony.torbs.count(), count)
