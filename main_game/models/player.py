from django.contrib.auth.models import User
from django.db import models
from polymorphic.models import PolymorphicModel


class Player(PolymorphicModel):
    name = models.CharField(max_length=255)
    user = models.OneToOneField(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="players",
    )
    polymorphic_ctype = models.ForeignKey(
        "contenttypes.ContentType",
        editable=False,
        null=True,
        on_delete=models.CASCADE,
        related_name="polymorphic_%(app_label)s.%(class)s_set+",
    )

    @property
    def is_human(self):
        return self.user is not None

    def save(self, *args, **kwargs):
        if not self.pk and self.user:
            self.name = self.user.username
        super().save(*args, **kwargs)

    def get_colonies(self):
        return self.colonies.all()

    def __str__(self):
        return f"Player {self.name}"


class AIPlayer(Player):
    difficulty = models.IntegerField(default=10)
