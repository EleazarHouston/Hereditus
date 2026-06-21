from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import connection, connections
from django.test import TransactionTestCase

from main_game.models import StoryText, Torb
from main_game.services.round_resolution import RoundService
from main_game.tests.factories import ColonyFactory, GameFactory, TorbFactory


@pytest.mark.concurrency
class ConcurrentRoundResolutionTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL is required for row-locking concurrency tests")
        self.game = GameFactory()
        self.first = ColonyFactory(game=self.game, name="First", food=20)
        self.second = ColonyFactory(game=self.game, name="Second", food=20)
        for colony in (self.first, self.second):
            first_parent = TorbFactory(
                colony=colony,
                private_ID=1,
                action=Torb.Action.GATHERING,
            )
            second_parent = TorbFactory(
                colony=colony,
                private_ID=2,
                action=Torb.Action.GATHERING,
            )
            TorbFactory(
                colony=colony,
                private_ID=3,
                action=Torb.Action.GATHERING,
            )
            TorbFactory(
                colony=colony,
                private_ID=4,
                action=Torb.Action.RESEARCHING,
                genes={
                    "vitality": [5, 5],
                    "sturdiness": [5, 5],
                    "agility": [5, 5],
                    "strength": [5, 5],
                    "intelligence": [1],
                },
            )
            colony.set_breed_torbs([first_parent.pk, second_parent.pk])

    def test_simultaneous_final_ready_requests_resolve_every_phase_once(self):
        barrier = Barrier(2)

        def ready(colony_id):
            connections.close_all()
            barrier.wait()
            try:
                return RoundService.ready_colony(colony_id, seed=99)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(ready, [self.first.pk, self.second.pk]))

        self.game.refresh_from_db()
        self.assertEqual(results.count(True), 1)
        self.assertEqual(results.count(False), 1)
        self.assertEqual(self.game.round_number, 2)
        self.assertEqual(self.game.round_seed, 99)
        for colony in (self.first, self.second):
            colony.refresh_from_db()
            colony.lab.refresh_from_db()
            self.assertFalse(colony.ready)
            self.assertEqual(colony.food, 17)
            self.assertEqual(colony.lab.science_points, 1)
            self.assertEqual(colony.torbs.count(), 5)
            self.assertEqual(
                StoryText.objects.filter(
                    colony=colony,
                    story_text_type="breeding",
                ).count(),
                1,
            )
            self.assertEqual(
                StoryText.objects.filter(
                    colony=colony,
                    story_text_type="science",
                    story_text="Your Torbs gleaned 1 science.",
                ).count(),
                1,
            )
            self.assertEqual(
                StoryText.objects.filter(
                    colony=colony,
                    story_text="Your Torbs gathered 2 food.",
                ).count(),
                1,
            )
            self.assertEqual(
                StoryText.objects.filter(
                    colony=colony,
                    story_text="It is now year 2.",
                ).count(),
                1,
            )
