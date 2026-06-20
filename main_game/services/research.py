import random

from django.db import transaction

from main_game.models import StoryText


class ResearchService:
    @staticmethod
    @transaction.atomic
    def conduct_research(lab, rng=None):
        rng = rng or random.Random()
        contribution = 0
        for torb in lab.colony.torbs.filter(action="researching"):
            intelligence = torb.genes.get("intelligence") or [0]
            contribution += 1 + int(rng.choice(intelligence) * rng.random())
        lab.science_points += contribution
        lab.save(update_fields=["science_points"])
        StoryText.objects.create(
            colony=lab.colony,
            story_text_type="science",
            story_text=f"Your Torbs gleaned {contribution} science.",
        )
        return contribution

    @staticmethod
    @transaction.atomic
    def make_mutagen(lab, science_points_used):
        science_points_used = int(science_points_used)
        if science_points_used < 10 or science_points_used % 10:
            raise ValueError("Science points must be a positive multiple of 10.")
        if lab.science_points < science_points_used:
            raise ValueError("Not enough science points to make mutagen.")
        mutagen_amount = science_points_used // 10
        lab.science_points -= science_points_used
        lab.mutagen += mutagen_amount
        lab.save(update_fields=["science_points", "mutagen"])
        StoryText.objects.create(
            colony=lab.colony,
            story_text_type="science",
            story_text=f"Your lab made {mutagen_amount} mutagen.",
        )
        return mutagen_amount

    @staticmethod
    @transaction.atomic
    def unlock_discovery(lab, discovery):
        if lab.discoveries.filter(pk=discovery.pk).exists():
            raise ValueError("Discovery already unlocked.")
        if lab.science_points < discovery.research_cost:
            raise ValueError("Not enough science points for this discovery.")
        lab.science_points -= discovery.research_cost
        lab.save(update_fields=["science_points"])
        lab.discoveries.add(discovery)
        StoryText.objects.create(
            colony=lab.colony,
            story_text_type="science",
            story_text=f"Your lab unlocked '{discovery.name}'.",
        )
