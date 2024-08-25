from django.contrib import admin

from .models import Torb, Colony, Game, EvolutionEngine

admin.site.register(Torb)
admin.site.register(Colony)
admin.site.register(Game)
admin.site.register(EvolutionEngine)

