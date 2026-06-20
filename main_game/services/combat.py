import random


class CombatService:
    @staticmethod
    def set_target(*, colony, action, target_id):
        if action == "scout":
            colony.army.set_scout_target(target_id)
        elif action == "attack":
            colony.army.set_attack_target(target_id)
        else:
            raise ValueError(f"Unsupported combat action: {action}")

    @staticmethod
    def resolve_round(army, rng=None):
        army.new_round(rng=rng or random.Random())
