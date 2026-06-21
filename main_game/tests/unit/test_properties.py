import copy
import random

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase

from main_game.models import ArmyTorb, Torb
from main_game.services.actions import ActionService
from main_game.services.research import ResearchService
from main_game.tests.factories import ColonyFactory, DiscoveryFactory, TorbFactory

PROPERTY_SETTINGS = settings(
    max_examples=20,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
GENE_NAMES = ("vitality", "sturdiness", "agility", "strength", "intelligence")
GENES = st.fixed_dictionaries(
    {
        gene: st.lists(st.integers(min_value=1, max_value=20), min_size=1, max_size=4)
        for gene in GENE_NAMES
    }
)


@st.composite
def health_and_adjustments(draw):
    maximum = draw(st.integers(min_value=1, max_value=100))
    current = draw(st.integers(min_value=1, max_value=maximum))
    adjustments = draw(
        st.lists(st.integers(min_value=-250, max_value=250), min_size=1, max_size=30)
    )
    return maximum, current, adjustments


@st.composite
def science_ledger(draw):
    initial = draw(st.integers(min_value=0, max_value=1_000))
    mutagen_units = draw(st.integers(min_value=0, max_value=initial // 10))
    remaining = initial - mutagen_units * 10
    discovery_cost = draw(st.integers(min_value=0, max_value=remaining))
    return initial, mutagen_units, discovery_cost


class ResourceInvariantProperties(TestCase):
    @PROPERTY_SETTINGS
    @given(
        food=st.integers(min_value=0, max_value=1_000),
        morale=st.integers(min_value=0, max_value=100),
        adjustments=st.lists(
            st.integers(min_value=-2_000, max_value=2_000), min_size=1, max_size=30
        ),
    )
    def test_food_and_morale_stay_in_range(self, food, morale, adjustments):
        colony = ColonyFactory(food=food)
        army = colony.army
        army.morale = morale
        army.save(update_fields=["morale"])

        for adjustment in adjustments:
            colony.adjust_food(adjustment)
            army.adjust_morale(adjustment)
            colony.refresh_from_db()
            army.refresh_from_db()
            self.assertGreaterEqual(colony.food, 0)
            self.assertGreaterEqual(army.morale, 0)
            self.assertLessEqual(army.morale, 100)

    @PROPERTY_SETTINGS
    @given(case=health_and_adjustments())
    def test_hp_stays_between_zero_and_max_hp(self, case):
        maximum, current, adjustments = case
        torb = TorbFactory(max_hp=maximum, hp=current)

        for adjustment in adjustments:
            torb.adjust_hp(adjustment, context="property test")
            torb.refresh_from_db()
            self.assertGreaterEqual(torb.hp, 0)
            self.assertLessEqual(torb.hp, torb.max_hp)


class ActionInvariantProperties(TestCase):
    @PROPERTY_SETTINGS
    @given(action=st.sampled_from(list(Torb.Action.values)))
    def test_dead_torbs_cannot_be_assigned_actions(self, action):
        colony = ColonyFactory()
        torb = TorbFactory(
            colony=colony,
            private_ID=1,
            is_alive=False,
            fertile=False,
            hp=0,
            action=Torb.Action.DEAD,
        )

        torb.set_action(action)
        torb.refresh_from_db()
        self.assertEqual(torb.action, Torb.Action.DEAD)

        with self.assertRaisesMessage(ValueError, "Dead or juvenile Torbs cannot act"):
            ActionService.perform(
                player=colony.player,
                colony=colony,
                action="gather",
                torb_ids=[torb.pk],
            )

    @PROPERTY_SETTINGS
    @given(
        population_size=st.integers(min_value=1, max_value=6),
        operations=st.lists(
            st.tuples(
                st.integers(min_value=0, max_value=20),
                st.sampled_from(("enlist", "train", "gather", "purge", "kill")),
            ),
            min_size=1,
            max_size=30,
        ),
    )
    def test_action_sequences_keep_one_army_membership_per_torb(self, population_size, operations):
        colony = ColonyFactory()
        torbs = [
            TorbFactory(colony=colony, private_ID=index + 1) for index in range(population_size)
        ]

        for index, operation in operations:
            torb = torbs[index % population_size]
            torb.refresh_from_db()
            if operation == "enlist" and torb.is_alive:
                ActionService.perform(
                    player=colony.player,
                    colony=colony,
                    action="enlist",
                    torb_ids=[torb.pk],
                )
            elif operation == "train":
                colony.army.train_soldiers(rng=random.Random(index))
            elif operation == "gather" and torb.is_alive:
                ActionService.perform(
                    player=colony.player,
                    colony=colony,
                    action="gather",
                    torb_ids=[torb.pk],
                )
            elif operation == "purge":
                colony.army.purge_soldiers()
            elif operation == "kill" and torb.is_alive:
                torb.adjust_hp(-torb.max_hp, context="property test")

            for population_torb in torbs:
                population_torb.refresh_from_db()
                membership_count = ArmyTorb.objects.filter(torb=population_torb).count()
                self.assertLessEqual(membership_count, 1)
                if population_torb.action == Torb.Action.SOLDIERING:
                    self.assertEqual(membership_count, 1)
                if not population_torb.is_alive:
                    self.assertEqual(membership_count, 0)


class GeneticsInvariantProperties(TestCase):
    @PROPERTY_SETTINGS
    @given(first_genes=GENES, second_genes=GENES, allele_limit=st.integers(1, 4))
    def test_breeding_preserves_parents_and_bounds_child_genes(
        self, first_genes, second_genes, allele_limit
    ):
        colony = ColonyFactory()
        engine = colony.game.evolution_engine_instance
        engine.alleles_per_gene = allele_limit
        engine.mutation_chance = 0
        first = TorbFactory(
            colony=colony,
            private_ID=1,
            genes=first_genes,
            hp=first_genes["vitality"][0],
            max_hp=first_genes["vitality"][0],
        )
        second = TorbFactory(
            colony=colony,
            private_ID=2,
            genes=second_genes,
            hp=second_genes["vitality"][0],
            max_hp=second_genes["vitality"][0],
        )
        original_first = copy.deepcopy(first.genes)
        original_second = copy.deepcopy(second.genes)

        child = engine.breed_torbs(colony, first, second, rng=random.Random(0))

        self.assertTrue(child)
        for gene in GENE_NAMES:
            expected_length = min(
                allele_limit,
                len(first_genes[gene]),
                len(second_genes[gene]),
            )
            self.assertEqual(len(child.genes[gene]), expected_length)
            self.assertTrue(all(allele >= 1 for allele in child.genes[gene]))
        self.assertGreaterEqual(child.hp, 0)
        self.assertLessEqual(child.hp, child.max_hp)
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.genes, original_first)
        self.assertEqual(second.genes, original_second)


class ScienceInvariantProperties(TestCase):
    @PROPERTY_SETTINGS
    @given(ledger=science_ledger())
    def test_science_spending_is_exactly_conserved(self, ledger):
        initial, mutagen_units, discovery_cost = ledger
        colony = ColonyFactory()
        lab = colony.lab
        lab.science_points = initial
        lab.save(update_fields=["science_points"])

        if mutagen_units:
            made = ResearchService.make_mutagen(lab, mutagen_units * 10)
            self.assertEqual(made, mutagen_units)
        discovery = DiscoveryFactory(research_cost=discovery_cost)
        ResearchService.unlock_discovery(lab, discovery)

        lab.refresh_from_db()
        self.assertGreaterEqual(lab.science_points, 0)
        self.assertGreaterEqual(lab.mutagen, 0)
        self.assertTrue(lab.discoveries.filter(pk=discovery.pk).exists())
        self.assertEqual(
            initial,
            lab.science_points + lab.mutagen * 10 + discovery.research_cost,
        )
