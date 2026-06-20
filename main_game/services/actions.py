from django.core.exceptions import PermissionDenied
from django.db import transaction

from main_game.models import Colony, Discovery, Torb
from main_game.services.combat import CombatService
from main_game.services.research import ResearchService
from main_game.services.round_resolution import RoundService


class ActionService:
    ACTION_PAYLOADS = {
        "breed": {"torb_ids"},
        "gather": {"torb_ids"},
        "enlist": {"torb_ids"},
        "scout": {"target_colony_id"},
        "attack": {"target_colony_id"},
        "end_turn": set(),
        "research": {"torb_ids"},
        "make_mutagen": {"science_points_used"},
        "purchase_discovery": {"discovery_id"},
    }

    @classmethod
    @transaction.atomic
    def perform(cls, *, player, colony, action, **kwargs):
        if colony.player_id != player.id:
            raise PermissionDenied("Player does not own this colony.")
        cls._validate_payload(action, kwargs)

        if action == "breed":
            torbs = cls._selected_torbs(colony, kwargs["torb_ids"])
            colony.set_breed_torbs([torb.pk for torb in torbs])
        elif action == "gather":
            torbs = cls._selected_torbs(colony, kwargs["torb_ids"])
            colony.assign_torbs_action([torb.pk for torb in torbs], Torb.Action.GATHERING)
        elif action == "enlist":
            torbs = cls._selected_torbs(colony, kwargs["torb_ids"])
            colony.assign_torbs_action([torb.pk for torb in torbs], Torb.Action.TRAINING)
        elif action in {"scout", "attack"}:
            target = cls._target_colony(colony, action, kwargs.get("target_colony_id"))
            CombatService.set_target(
                colony=colony,
                action=action,
                target_id=target.pk if target else None,
            )
        elif action == "end_turn":
            RoundService.ready_colony(colony.pk)
        elif action == "research":
            torbs = cls._selected_torbs(colony, kwargs["torb_ids"])
            colony.assign_torbs_action([torb.pk for torb in torbs], Torb.Action.RESEARCHING)
        elif action == "make_mutagen":
            ResearchService.make_mutagen(colony.lab, kwargs["science_points_used"])
        elif action == "purchase_discovery":
            discovery_id = kwargs["discovery_id"]
            if not isinstance(discovery_id, int) or isinstance(discovery_id, bool):
                raise ValueError("discovery_id must be an integer.")
            discovery = Discovery.objects.get(pk=discovery_id)
            ResearchService.unlock_discovery(colony.lab, discovery)

    @classmethod
    def _validate_payload(cls, action, kwargs):
        if action not in cls.ACTION_PAYLOADS:
            raise ValueError(f"Unknown action: {action}")
        expected = cls.ACTION_PAYLOADS[action]
        supplied = set(kwargs)
        if supplied != expected:
            raise ValueError(
                f"Invalid payload for {action}: expected {sorted(expected)}, got {sorted(supplied)}."
            )

    @staticmethod
    def _selected_torbs(colony, torb_ids):
        if not isinstance(torb_ids, (list, tuple)) or not torb_ids:
            raise ValueError("torb_ids must be a non-empty list of integers.")
        if any(not isinstance(torb_id, int) or isinstance(torb_id, bool) for torb_id in torb_ids):
            raise ValueError("torb_ids must be a non-empty list of integers.")
        if len(set(torb_ids)) != len(torb_ids):
            raise ValueError("torb_ids must not contain duplicates.")
        torbs = list(Torb.objects.filter(pk__in=torb_ids, colony=colony).order_by("pk"))
        if len(torbs) != len(torb_ids):
            raise ValueError("Every Torb must belong to the acting colony.")
        if any(not torb.is_alive or torb.growing for torb in torbs):
            raise ValueError("Dead or juvenile Torbs cannot act.")
        return torbs

    @staticmethod
    def _target_colony(colony, action, target_id):
        if target_id is None:
            return None
        if not isinstance(target_id, int) or isinstance(target_id, bool):
            raise ValueError("target_colony_id must be an integer or null.")
        try:
            target = Colony.objects.get(pk=target_id, game=colony.game)
        except Colony.DoesNotExist as error:
            raise ValueError("Target colony must belong to the same game.") from error
        if target.pk == colony.pk:
            raise ValueError("A colony cannot target itself.")
        if action == "attack" and not colony.discovered_colonies.filter(pk=target.pk).exists():
            raise ValueError("Attack target must be discovered first.")
        return target
