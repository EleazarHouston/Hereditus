from django.contrib.auth.models import User
from django.db import models


class Game(models.Model):
    class RoundStatus(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVING = "resolving", "Resolving"
        COMPLETE = "complete", "Complete"

    starting_torbs = models.IntegerField(default=4)
    description = models.CharField(max_length=256, null=True)
    round_number = models.IntegerField(default=1)
    round_status = models.CharField(
        max_length=16,
        choices=RoundStatus.choices,
        default=RoundStatus.OPEN,
    )
    round_seed = models.PositiveBigIntegerField(null=True, blank=True)
    private = models.BooleanField(default=False)
    allowed_players = models.ManyToManyField(User, blank=True)
    closed = models.BooleanField(default=False)
    max_colonies_per_player = models.IntegerField(default=1)

    def __str__(self):
        return self.description or f"Game {self.pk}"

    @property
    def unready_colonies(self):
        return self.colony_set.filter(ready=False).count()
