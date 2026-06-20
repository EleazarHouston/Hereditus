from django.core.exceptions import PermissionDenied
from django.db import transaction

from main_game.models import Colony, Discovery
from main_game.services.combat import CombatService
from main_game.services.research import ResearchService
from main_game.services.round_resolution import RoundService


class ActionService:
    @staticmethod
    @transaction.atomic
    def perform(*, player, colony, action, **kwargs):
        if colony.player_id != player.id:
            raise PermissionDenied("Player does not own this colony.")

        if action == "breed":
            colony.set_breed_torbs(kwargs.get("torb_ids"))
        elif action == "gather":
            colony.assign_torbs_action(kwargs.get("torb_ids"), "gathering")
        elif action == "enlist":
            colony.assign_torbs_action(kwargs.get("torb_ids"), "training")
        elif action in {"scout", "attack"}:
            target_id = kwargs.get("target_colony_id")
            target = None
            if target_id:
                target = Colony.objects.get(pk=target_id, game=colony.game)
            CombatService.set_target(
                colony=colony,
                action=action,
                target_id=target.pk if target else None,
            )
        elif action == "end_turn":
            RoundService.ready_colony(colony.pk)
        elif action == "research":
            colony.assign_torbs_action(kwargs.get("torb_ids"), "researching")
        elif action == "make_mutagen":
            ResearchService.make_mutagen(colony.lab, kwargs.get("science_points_used", 0))
        elif action == "purchase_discovery":
            discovery_id = kwargs.get("discovery_id")
            if discovery_id is None:
                raise ValueError("A discovery is required.")
            discovery = Discovery.objects.get(pk=discovery_id)
            ResearchService.unlock_discovery(colony.lab, discovery)
        else:
            raise ValueError(f"Unknown action: {action}")
