import factory
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

from main_game.models import (
    AIPlayer,
    Army,
    ArmyTorb,
    Colony,
    Discovery,
    Game,
    Lab,
    Player,
    Torb,
)
from main_game.services.colony_creation import ColonyService
from main_game.services.game_creation import GameService

DEFAULT_GENES = {
    "vitality": [5, 5],
    "sturdiness": [5, 5],
    "agility": [5, 5],
    "strength": [5, 5],
    "intelligence": [5, 5],
}


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda number: f"user-{number}")
    password = factory.LazyFunction(lambda: make_password("test-password"))


class PlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Player

    user = factory.SubFactory(UserFactory)


class AIPlayerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AIPlayer

    name = factory.Sequence(lambda number: f"AI Player {number}")
    user = None


class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Game

    description = factory.Sequence(lambda number: f"Test game {number}")
    starting_torbs = 0

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return GameService.create_game(**kwargs)


class ColonyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Colony

    name = factory.Sequence(lambda number: f"Test colony {number}")
    game = factory.SubFactory(GameFactory)
    player = factory.SubFactory(PlayerFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        return ColonyService.create_colony(**kwargs)


class TorbFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Torb

    colony = factory.SubFactory(ColonyFactory)
    private_ID = factory.Sequence(lambda number: number + 1)
    name = factory.Sequence(lambda number: f"Torb {number}")
    genes = factory.LazyFunction(lambda: {key: list(value) for key, value in DEFAULT_GENES.items()})


class LabFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Lab

    colony = factory.SubFactory(ColonyFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        colony = kwargs.pop("colony")
        lab, _ = model_class.objects.update_or_create(
            colony=colony,
            defaults=kwargs,
        )
        return lab


class DiscoveryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Discovery

    name = factory.Sequence(lambda number: f"Discovery {number}")
    description = factory.Faker("sentence")
    research_cost = 100


class ArmyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Army

    colony = factory.SubFactory(ColonyFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        colony = kwargs.pop("colony")
        army, _ = model_class.objects.update_or_create(
            colony=colony,
            defaults=kwargs,
        )
        return army


class ArmyTorbFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ArmyTorb

    army = factory.SubFactory(ArmyFactory)
    torb = factory.SubFactory(
        TorbFactory,
        colony=factory.SelfAttribute("..army.colony"),
    )
    active_alleles = factory.LazyFunction(
        lambda: {
            "strength": 5,
            "agility": 5,
            "vitality": 5,
            "sturdiness": 5,
        }
    )
