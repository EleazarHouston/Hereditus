import random

from main_game.services.actions import ActionService


class AIService:
    @staticmethod
    def make_decisions(colony, rng=None):
        rng = rng or random.Random()
        player = colony.player
        gathering_ids = list(
            colony.torbs.filter(action="gathering").order_by("pk").values_list("pk", flat=True)
        )

        if colony.food > 5 and colony.food > colony.torb_count // 2:
            rng.shuffle(gathering_ids)
            for _ in range(int(colony.torb_count**0.5)):
                pair = gathering_ids[:2]
                gathering_ids = gathering_ids[2:]
                if len(pair) < 2:
                    break
                ActionService.perform(player=player, colony=colony, action="breed", torb_ids=pair)

        if colony.torb_count > 6 and colony.food >= 5:
            desired = max(1, colony.torb_count // rng.randint(6, 10))
            current = colony.torbs.filter(action="training").count()
            selected = gathering_ids[: max(0, desired - current)]
            if selected:
                ActionService.perform(
                    player=player, colony=colony, action="enlist", torb_ids=selected
                )

        soldiers = colony.torbs.filter(action="soldiering")
        if soldiers.exists():
            targets = list(
                colony.game.colony_set.exclude(pk__in=colony.discovered_colonies.all())
                .order_by("pk")
                .values_list("pk", flat=True)
            )
            if targets:
                ActionService.perform(
                    player=player,
                    colony=colony,
                    action="scout",
                    target_colony_id=rng.choice(targets),
                )

        if soldiers.exists() and all(torb.hp == torb.max_hp for torb in soldiers):
            targets = list(
                colony.discovered_colonies.exclude(player=player)
                .order_by("pk")
                .values_list("pk", flat=True)
            )
            if targets:
                ActionService.perform(
                    player=player,
                    colony=colony,
                    action="attack",
                    target_colony_id=rng.choice(targets),
                )

        colony.ready = True
        colony.save(update_fields=["ready"])
