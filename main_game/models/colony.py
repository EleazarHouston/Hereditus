import random

from django.db import models

from .story_text import StoryText
from .torb_names import torb_names


class Colony(models.Model):
    player = models.ForeignKey(
        "Player",
        on_delete=models.PROTECT,
        related_name="colonies",
    )
    name = models.CharField(max_length=64, default="DefaultName")
    game = models.ForeignKey("main_game.Game", on_delete=models.CASCADE)
    food = models.IntegerField(default=5)
    ready = models.BooleanField(default=False)
    rest_heal_flat = models.IntegerField(default=2)
    rest_heal_perc = models.FloatField(default=0.2)
    gather_rate = models.FloatField(default=1.7)
    discovered_colonies = models.ManyToManyField(
        "self",
        symmetrical=False,
        related_name="discoverers",
        blank=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(food__gte=0),
                name="colony_food_nonnegative",
            ),
        ]

    @property
    def army(self):
        return self.army_instance

    @property
    def torb_count(self):
        return self.torbs.filter(is_alive=True).count()

    @property
    def num_soldiers(self):
        return self.torbs.filter(action="soldiering", is_alive=True).count()

    @property
    def num_training(self):
        return self.torbs.filter(action="training", is_alive=True).count()

    def new_round(self, round_number, rng=None):
        from main_game.services.combat import CombatService
        from main_game.services.research import ResearchService

        rng = rng or random.Random()
        self.reset_fertility()
        self.gather_phase()
        self.grow_torbs()
        self.call_breed_torbs(rng=rng)
        self.rest_torbs()
        CombatService.resolve_round(self.army, rng=rng)
        ResearchService.conduct_research(self.lab, rng=rng)
        self.colony_meal(rng=rng)
        StoryText.objects.create(
            colony=self,
            story_text_type="system",
            story_text=f"It is now year {round_number + 1}.",
        )

    def reset_fertility(self):
        self.torbs.filter(is_alive=True, growing=False).update(fertile=True)

    def gather_phase(self):
        gathered = round(self.torbs.filter(action="gathering").count() * self.gather_rate)
        self.adjust_food(gathered)
        StoryText.objects.create(
            colony=self,
            story_text_type="food",
            story_text=f"Your Torbs gathered {gathered} food.",
        )

    def grow_torbs(self):
        for torb in self.torbs.filter(growing=True):
            torb.growing = False
            torb.set_action(action="gathering")

    def call_breed_torbs(self, rng=None):
        checked = set()
        for torb in self.torbs.filter(action="breeding").select_related("context_torb"):
            if torb.pk in checked or not torb.context_torb_id:
                continue
            checked.update({torb.pk, torb.context_torb_id})
            partner = torb.context_torb
            if partner is None:
                continue
            new_torb = self.game.evolution_engine_instance.breed_torbs(
                colony=self,
                torb0=torb,
                torb1=partner,
                rng=rng,
            )
            if new_torb:
                StoryText.objects.create(
                    colony=self,
                    story_text_type="breeding",
                    story_text=f"A new Torb, '{new_torb.name}', was born.",
                )
            torb.set_action(action="gathering")
            partner.set_action(action="gathering")

    def rest_torbs(self):
        for torb in self.torbs.filter(action="resting", starving=False):
            amount = round(self.rest_heal_flat + self.rest_heal_perc * torb.max_hp)
            torb.adjust_hp(amount, context="resting")

    def colony_meal(self, rng=None):
        rng = rng or random.Random()
        living = list(self.torbs.filter(is_alive=True))
        hungry_count = max(0, len(living) - self.food)
        starved = set(rng.sample(living, hungry_count)) if hungry_count else set()
        eaten = 0
        for torb in living:
            if torb in starved:
                torb.starving = True
                torb.adjust_hp(-1, context="starvation")
            else:
                torb.starving = False
                torb.adjust_hp(1, context="eating a good meal")
                eaten += 1
        self.adjust_food(-eaten)
        StoryText.objects.create(
            colony=self,
            story_text_type="food",
            story_text=f"Your Torbs ate {eaten} food and {len(starved)} went hungry.",
        )

    def set_breed_torbs(self, torb_ids):
        from .torb import Torb

        if not torb_ids or len(torb_ids) != 2 or len(set(map(str, torb_ids))) != 2:
            raise ValueError("Breeding requires exactly two distinct Torbs.")
        torbs = list(
            Torb.objects.filter(
                pk__in=torb_ids,
                colony=self,
                is_alive=True,
                fertile=True,
                growing=False,
            ).order_by("pk")
        )
        if len(torbs) != 2:
            raise ValueError("Both Torbs must belong to this colony and be alive and fertile.")
        torbs[0].set_action(action="breeding", context_torb=torbs[1])
        torbs[1].set_action(action="breeding", context_torb=torbs[0])

    def assign_torbs_action(self, torb_ids, action):
        if not torb_ids:
            return
        for torb in self.torbs.filter(pk__in=torb_ids):
            torb.set_action(action=action)

    def reset_torbs_actions(self, action="gathering"):
        for torb in self.torbs.all():
            torb.set_action(action=action)

    def adjust_food(self, adjust_amount):
        self.food = max(self.food + int(adjust_amount), 0)
        self.save(update_fields=["food"])

    def new_torb(self, genes, generation, rng=None):
        from .torb import Torb

        rng = rng or random.Random()
        maximum = self.torbs.aggregate(max_id=models.Max("private_ID"))["max_id"]
        private_id = maximum + 1 if maximum is not None else 1
        used_names = set(self.torbs.values_list("name", flat=True))
        available = [name for name in torb_names if name not in used_names]
        if available:
            name = rng.choice(available)
        else:
            base = rng.choice(torb_names)
            counter = 2
            name = base
            while name in used_names:
                name = f"{base} {counter}"
                counter += 1
        max_hp = int(genes["vitality"][0])
        return Torb.objects.create(
            colony=self,
            private_ID=private_id,
            name=name,
            genes=genes,
            generation=generation,
            max_hp=max_hp,
            hp=max_hp,
        )

    def __str__(self):
        return self.name
