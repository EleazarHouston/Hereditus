import copy
import random

from django.test import TestCase

from main_game.models import StoryText, Torb
from main_game.tests.factories import ColonyFactory, TorbFactory


class ColonyPhaseTests(TestCase):
    def setUp(self):
        self.colony = ColonyFactory(food=5)

    def test_gathering_counts_only_living_gatherers(self):
        TorbFactory(colony=self.colony, private_ID=1, action=Torb.Action.GATHERING)
        TorbFactory(colony=self.colony, private_ID=2, action=Torb.Action.RESTING)
        TorbFactory(
            colony=self.colony,
            private_ID=3,
            action=Torb.Action.GATHERING,
            is_alive=False,
            fertile=False,
            hp=0,
        )

        self.colony.gather_phase()

        self.colony.refresh_from_db()
        self.assertEqual(self.colony.food, 7)
        self.assertTrue(
            StoryText.objects.filter(
                colony=self.colony, story_text="Your Torbs gathered 2 food."
            ).exists()
        )

    def test_growth_makes_juvenile_an_adult_gatherer(self):
        torb = TorbFactory(
            colony=self.colony,
            private_ID=1,
            growing=True,
            action=Torb.Action.GROWING,
        )

        self.colony.grow_torbs()

        torb.refresh_from_db()
        self.assertFalse(torb.growing)
        self.assertEqual(torb.action, Torb.Action.GATHERING)

    def test_breeding_phase_creates_one_juvenile_and_resets_parents(self):
        first = TorbFactory(colony=self.colony, private_ID=1)
        second = TorbFactory(colony=self.colony, private_ID=2)
        first_genes = copy.deepcopy(first.genes)
        second_genes = copy.deepcopy(second.genes)
        self.colony.set_breed_torbs([first.pk, second.pk])

        self.colony.call_breed_torbs(rng=random.Random(4))

        first.refresh_from_db()
        second.refresh_from_db()
        baby = self.colony.torbs.exclude(pk__in=[first.pk, second.pk]).get()
        self.assertTrue(baby.growing)
        self.assertFalse(baby.fertile)
        self.assertEqual(baby.action, Torb.Action.GROWING)
        self.assertEqual(first.action, Torb.Action.GATHERING)
        self.assertEqual(second.action, Torb.Action.GATHERING)
        self.assertEqual(first.genes, first_genes)
        self.assertEqual(second.genes, second_genes)

    def test_rest_heals_nonstarving_but_not_starving_torbs(self):
        rested = TorbFactory(
            colony=self.colony,
            private_ID=1,
            action=Torb.Action.RESTING,
            hp=1,
            max_hp=10,
        )
        starving = TorbFactory(
            colony=self.colony,
            private_ID=2,
            action=Torb.Action.RESTING,
            starving=True,
            hp=1,
            max_hp=10,
        )

        self.colony.rest_torbs()

        rested.refresh_from_db()
        starving.refresh_from_db()
        self.assertEqual(rested.hp, 5)
        self.assertEqual(starving.hp, 1)

    def test_meal_feeds_everyone_when_food_is_available(self):
        first = TorbFactory(
            colony=self.colony,
            private_ID=1,
            starving=True,
            hp=3,
            max_hp=5,
        )
        second = TorbFactory(colony=self.colony, private_ID=2, hp=4, max_hp=5)

        self.colony.colony_meal(rng=random.Random(0))

        self.colony.refresh_from_db()
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(self.colony.food, 3)
        self.assertFalse(first.starving)
        self.assertFalse(second.starving)
        self.assertEqual((first.hp, second.hp), (4, 5))

    def test_shortage_starves_only_unfed_torbs_without_negative_food(self):
        torbs = [
            TorbFactory(colony=self.colony, private_ID=index, hp=3, max_hp=5)
            for index in range(1, 4)
        ]
        self.colony.food = 1
        self.colony.save(update_fields=["food"])

        self.colony.colony_meal(rng=random.Random(1))

        self.colony.refresh_from_db()
        for torb in torbs:
            torb.refresh_from_db()
        starving = [torb for torb in torbs if torb.starving]
        fed = [torb for torb in torbs if not torb.starving]
        self.assertEqual(self.colony.food, 0)
        self.assertEqual(len(starving), 2)
        self.assertEqual(len(fed), 1)
        self.assertTrue(all(torb.hp == 2 for torb in starving))
        self.assertEqual(fed[0].hp, 4)

    def test_reset_fertility_excludes_dead_and_juvenile_torbs(self):
        adult = TorbFactory(colony=self.colony, private_ID=1, fertile=False)
        juvenile = TorbFactory(colony=self.colony, private_ID=2, fertile=False, growing=True)
        dead = TorbFactory(
            colony=self.colony,
            private_ID=3,
            fertile=False,
            is_alive=False,
            hp=0,
        )

        self.colony.reset_fertility()

        adult.refresh_from_db()
        juvenile.refresh_from_db()
        dead.refresh_from_db()
        self.assertTrue(adult.fertile)
        self.assertFalse(juvenile.fertile)
        self.assertFalse(dead.fertile)
