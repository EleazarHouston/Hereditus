import random
from unittest.mock import patch

import pytest
from django.db import connection
from django.test import TestCase

from main_game.models import ArmyTorb, Discovery, StoryText, Torb
from main_game.services.actions import ActionService
from main_game.services.ai import AIService
from main_game.tests.factories import (
    AIPlayerFactory,
    ColonyFactory,
    DiscoveryFactory,
    GameFactory,
    PlayerFactory,
    TorbFactory,
)


@pytest.mark.integration
class MultiplayerSimulationTests(TestCase):
    rounds = 20

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("The multiplayer simulation requires PostgreSQL")
        self.game = GameFactory(starting_torbs=0)
        self.humans = [
            ColonyFactory(
                game=self.game,
                player=PlayerFactory(),
                name=f"Human {index}",
                food=200 if index < 2 else 0,
            )
            for index in range(3)
        ]
        self.ai = ColonyFactory(
            game=self.game,
            player=AIPlayerFactory(),
            name="AI",
            food=100,
        )
        self.colonies = [*self.humans, self.ai]
        self.discoveries = [
            DiscoveryFactory(name="Agronomy", research_cost=1),
            DiscoveryFactory(name="Genomics", research_cost=5),
        ]
        for colony in self.colonies:
            for private_id in range(1, 7):
                genes = self._genes(colony, private_id)
                vitality = genes["vitality"][0]
                TorbFactory(
                    colony=colony,
                    private_ID=private_id,
                    genes=genes,
                    hp=3 if colony == self.humans[2] else vitality,
                    max_hp=vitality,
                )

    @staticmethod
    def _genes(colony, private_id):
        if colony.name == "Human 0" and private_id == 1:
            values = {"vitality": 10, "sturdiness": 10, "agility": 10, "strength": 10}
        elif colony.name == "Human 1" and private_id == 4:
            values = {"vitality": 3, "sturdiness": 1, "agility": 1, "strength": 1}
        else:
            values = {"vitality": 5, "sturdiness": 5, "agility": 5, "strength": 5}
        return {
            **{name: [value] for name, value in values.items()},
            "intelligence": [5],
        }

    @staticmethod
    def _act(colony, action, **kwargs):
        return ActionService.perform(
            player=colony.player,
            colony=colony,
            action=action,
            **kwargs,
        )

    def _schedule_human_actions(self, round_number):
        attacker, defender, starving = self.humans
        if round_number == 1:
            self._act(attacker, "enlist", torb_ids=[attacker.torbs.get(private_ID=1).pk])
            self._act(attacker, "research", torb_ids=[attacker.torbs.get(private_ID=2).pk])
            self._act(
                attacker,
                "breed",
                torb_ids=list(
                    attacker.torbs.filter(private_ID__in=[3, 4]).values_list("pk", flat=True)
                ),
            )
            self._act(defender, "research", torb_ids=[defender.torbs.get(private_ID=1).pk])
            self._act(
                defender,
                "breed",
                torb_ids=list(
                    defender.torbs.filter(private_ID__in=[2, 3]).values_list("pk", flat=True)
                ),
            )
            self._act(
                starving,
                "research",
                torb_ids=list(starving.torbs.values_list("pk", flat=True)),
            )
        if round_number == 2:
            self._act(attacker, "scout", target_colony_id=defender.pk)
            self._act(
                attacker,
                "purchase_discovery",
                discovery_id=self.discoveries[0].pk,
            )
        if round_number == 3:
            self._act(defender, "enlist", torb_ids=[defender.torbs.get(private_ID=4).pk])
        if round_number >= 4:
            soldier = attacker.torbs.filter(
                action=Torb.Action.SOLDIERING,
                is_alive=True,
            ).first()
            if soldier and attacker.discovered_colonies.filter(pk=defender.pk).exists():
                self._act(attacker, "attack", target_colony_id=defender.pk)
        if round_number in {3, 7, 11, 15, 19}:
            for colony in (attacker, defender):
                pair = list(
                    colony.torbs.filter(
                        action=Torb.Action.GATHERING,
                        is_alive=True,
                        fertile=True,
                        growing=False,
                    )
                    .order_by("pk")
                    .values_list("pk", flat=True)[:2]
                )
                if len(pair) == 2:
                    self._act(colony, "breed", torb_ids=pair)
        if round_number == 6 and attacker.lab.science_points >= self.discoveries[1].research_cost:
            self._act(
                attacker,
                "purchase_discovery",
                discovery_id=self.discoveries[1].pk,
            )
        if round_number == 10 and attacker.lab.science_points >= 10:
            spend = attacker.lab.science_points // 10 * 10
            self._act(attacker, "make_mutagen", science_points_used=spend)

    def _assert_reload_stable(self, instance, fields):
        before = tuple(getattr(instance, field) for field in fields)
        instance.refresh_from_db()
        self.assertEqual(before, tuple(getattr(instance, field) for field in fields))

    def _assert_invariants(self, previous_round, story_ids, ai_reset_observations):
        self.game.refresh_from_db()
        self._assert_reload_stable(
            self.game,
            ["round_number", "round_status", "round_seed", "closed"],
        )
        self._assert_reload_stable(
            self.game.evolution_engine_instance,
            ["mutation_chance", "mutation_dev", "alleles_per_gene", "gene_list"],
        )
        for player in [colony.player for colony in self.colonies]:
            fields = ["name", "user_id", "polymorphic_ctype_id"]
            if hasattr(player, "difficulty"):
                fields.append("difficulty")
            self._assert_reload_stable(player, fields)
        self.assertEqual(self.game.round_number, previous_round + 1)
        self.assertEqual(self.game.round_status, self.game.RoundStatus.OPEN)
        for colony in self.humans:
            colony.refresh_from_db()
            self.assertFalse(colony.ready)
        self.ai.refresh_from_db()
        self.assertTrue(self.ai.ready)
        self.assertFalse(ai_reset_observations[-1])

        new_stories = StoryText.objects.exclude(pk__in=story_ids)
        self.assertTrue(new_stories.exists())
        wrong_round_stories = list(
            new_stories.exclude(game_round__in=[previous_round, previous_round + 1]).values_list(
                "story_text", "game_round", "colony__name"
            )
        )
        self.assertEqual(wrong_round_stories, [])
        self.assertFalse(
            new_stories.filter(game_round=previous_round + 1).exclude(colony=self.ai).exists()
        )
        self.assertTrue(
            new_stories.filter(
                game_round=previous_round,
                story_text=f"It is now year {previous_round + 1}.",
            ).exists()
        )

        for colony in self.colonies:
            colony.refresh_from_db()
            colony.lab.refresh_from_db()
            colony.army.refresh_from_db()
            self._assert_reload_stable(
                colony,
                ["player_id", "game_id", "food", "ready", "name"],
            )
            self._assert_reload_stable(
                colony.lab,
                ["colony_id", "science_points", "mutagen"],
            )
            self._assert_reload_stable(
                colony.army,
                ["colony_id", "scout_target_id", "attack_target_id", "morale"],
            )
            self.assertEqual(colony.game_id, self.game.pk)
            self.assertEqual(colony.player.colonies.get(pk=colony.pk), colony)
            self.assertGreaterEqual(colony.food, 0)
            self.assertGreaterEqual(colony.lab.science_points, 0)
            self.assertGreaterEqual(colony.lab.mutagen, 0)
            self.assertGreaterEqual(colony.army.morale, 0)
            self.assertLessEqual(colony.army.morale, 100)
            self.assertFalse(colony.discovered_colonies.exclude(game_id=self.game.pk).exists())
            for target in (colony.army.scout_target, colony.army.attack_target):
                if target is not None:
                    self.assertEqual(target.game_id, self.game.pk)

            for torb in colony.torbs.select_related("context_torb").all():
                state = (
                    torb.hp,
                    torb.max_hp,
                    torb.is_alive,
                    torb.action,
                    torb.context_torb_id,
                    torb.starving,
                )
                torb.refresh_from_db()
                self.assertEqual(
                    state,
                    (
                        torb.hp,
                        torb.max_hp,
                        torb.is_alive,
                        torb.action,
                        torb.context_torb_id,
                        torb.starving,
                    ),
                )
                self.assertEqual(torb.colony_id, colony.pk)
                self.assertGreaterEqual(torb.hp, 0)
                self.assertLessEqual(torb.hp, torb.max_hp)
                memberships = ArmyTorb.objects.filter(torb=torb)
                for membership in memberships:
                    self._assert_reload_stable(
                        membership,
                        ["army_id", "torb_id", "active_alleles"],
                    )
                if torb.is_alive and torb.action == Torb.Action.SOLDIERING:
                    self.assertEqual(memberships.count(), 1)
                    self.assertEqual(memberships.get().army_id, colony.army.pk)
                else:
                    self.assertFalse(memberships.exists())
                if torb.action == Torb.Action.BREEDING:
                    self.assertIsNotNone(torb.context_torb)
                    self.assertEqual(torb.context_torb.action, Torb.Action.BREEDING)
                    self.assertEqual(torb.context_torb.context_torb_id, torb.pk)
                else:
                    self.assertIsNone(torb.context_torb_id)

        for discovery in Discovery.objects.all():
            self._assert_reload_stable(
                discovery,
                ["name", "description", "research_cost"],
            )
            self.assertGreaterEqual(discovery.research_cost, 0)
        for story in new_stories:
            state = (story.story_text, story.story_text_type, story.game_round)
            story.refresh_from_db()
            self.assertEqual(state, (story.story_text, story.story_text_type, story.game_round))

    def test_twenty_round_seeded_multiplayer_simulation(self):
        seeds = [10_000 + number for number in range(self.rounds)]
        ai_reset_observations = []
        training_seen = False
        original_ai = AIService.make_decisions

        def observed_ai(colony, rng=None):
            colony.refresh_from_db(fields=["ready"])
            ai_reset_observations.append(colony.ready)
            return original_ai(colony, rng=rng)

        with (
            patch.object(AIService, "make_decisions", side_effect=observed_ai),
            patch(
                "main_game.services.round_resolution.secrets.randbits",
                side_effect=seeds,
            ),
        ):
            AIService.make_decisions(self.ai, rng=random.Random(9_999))
            for expected_seed in seeds:
                self.game.refresh_from_db()
                previous_round = self.game.round_number
                story_ids = list(StoryText.objects.values_list("pk", flat=True))
                self._schedule_human_actions(previous_round)
                for colony in self.humans:
                    self._act(colony, "end_turn")
                self.game.refresh_from_db()
                self.assertEqual(self.game.round_seed, expected_seed)
                self._assert_invariants(
                    previous_round,
                    story_ids,
                    ai_reset_observations,
                )
                training_seen = training_seen or ArmyTorb.objects.exists()

        self.assertEqual(len(ai_reset_observations), self.rounds + 1)
        self.assertTrue(training_seen)
        self.assertTrue(StoryText.objects.filter(story_text_type="breeding").exists())
        self.assertTrue(StoryText.objects.filter(story_text_type="science").exists())
        self.assertTrue(StoryText.objects.filter(story_text_type="scout").exists())
        self.assertTrue(StoryText.objects.filter(story_text_type="combat").exists())
        self.assertTrue(StoryText.objects.filter(story_text_type="death").exists())
        self.assertTrue(StoryText.objects.filter(story_text__contains="went hungry").exists())
        self.assertTrue(self.humans[0].lab.discoveries.exists())
