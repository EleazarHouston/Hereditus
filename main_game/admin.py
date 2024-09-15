from django.contrib import admin

from .models import Torb, Colony, Game, EvolutionEngine, StoryText, Army, ArmyTorb

admin.site.register(Torb)
admin.site.register(Colony)
admin.site.register(Game)
admin.site.register(EvolutionEngine)
admin.site.register(StoryText)
admin.site.register(Army)
admin.site.register(ArmyTorb)