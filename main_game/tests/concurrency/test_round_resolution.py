from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from django.db import connection, connections
from django.test import TransactionTestCase

from main_game.services.round_resolution import RoundService
from main_game.tests.factories import ColonyFactory, GameFactory


@pytest.mark.concurrency
class ConcurrentRoundResolutionTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("PostgreSQL is required for row-locking concurrency tests")
        self.game = GameFactory()
        self.first = ColonyFactory(game=self.game, name="First")
        self.second = ColonyFactory(game=self.game, name="Second")

    def test_simultaneous_final_ready_requests_advance_exactly_once(self):
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
        self.first.refresh_from_db()
        self.second.refresh_from_db()
        self.assertEqual(results.count(True), 1)
        self.assertEqual(self.game.round_number, 2)
        self.assertFalse(self.first.ready)
        self.assertFalse(self.second.ready)
