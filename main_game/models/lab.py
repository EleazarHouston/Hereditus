from django.db import models


class Lab(models.Model):
    colony = models.OneToOneField(
        "Colony",
        on_delete=models.CASCADE,
        related_name="lab",
    )
    science_points = models.IntegerField(default=0)
    discoveries = models.ManyToManyField(
        "main_game.Discovery",
        related_name="labs",
        blank=True,
    )
    mutagen = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(science_points__gte=0),
                name="lab_science_points_nonnegative",
            ),
            models.CheckConstraint(
                condition=models.Q(mutagen__gte=0),
                name="lab_mutagen_nonnegative",
            ),
        ]


class Discovery(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    research_cost = models.IntegerField(default=100)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(research_cost__gte=0),
                name="discovery_research_cost_nonnegative",
            )
        ]

    def __str__(self):
        return self.name
