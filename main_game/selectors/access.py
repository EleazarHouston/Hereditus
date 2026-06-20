from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from main_game.models import Colony


def get_owned_colony(user, colony_id):
    colony = get_object_or_404(
        Colony.objects.select_related("player__user", "game"),
        pk=colony_id,
    )
    if colony.player.user_id != user.id:
        raise PermissionDenied("You do not own this colony.")
    return colony
