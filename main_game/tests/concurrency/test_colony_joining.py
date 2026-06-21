from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import connection, connections
from django.test import TransactionTestCase

from main_game.models import Army, Lab, StoryText
from main_game.services.colony_creation import ColonyService
from main_game.tests.factories import GameFactory, UserFactory


@pytest.mark.concurrency
class ConcurrentColonyJoiningTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL is required for row-locking concurrency tests")
        self.game = GameFactory(max_colonies_per_player=2)
        self.user = UserFactory()

    def test_concurrent_joining_never_exceeds_player_cap(self):
        worker_count = 4
        barrier = Barrier(worker_count)

        def join(index):
            connections.close_all()
            barrier.wait()
            try:
                colony = ColonyService.join_game(
                    game_id=self.game.pk,
                    user=self.user,
                    name=f"Concurrent {index}",
                )
                return "joined", colony.pk
            except ValueError:
                return "rejected", None
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            results = list(executor.map(join, range(worker_count)))

        colonies = self.game.colony_set.filter(player__user=self.user)
        self.assertEqual([status for status, _ in results].count("joined"), 2)
        self.assertEqual([status for status, _ in results].count("rejected"), 2)
        self.assertEqual(colonies.count(), 2)
        self.assertEqual(Army.objects.filter(colony__in=colonies).count(), 2)
        self.assertEqual(Lab.objects.filter(colony__in=colonies).count(), 2)
        self.assertEqual(
            StoryText.objects.filter(
                colony__in=colonies,
                story_text="Welcome to Hereditus!",
            ).count(),
            2,
        )
