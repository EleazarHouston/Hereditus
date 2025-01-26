from django.contrib import admin
from .models import Torb, Colony, Game, EvolutionEngine, StoryText, Army, ArmyTorb, Player

class TorbAdmin(admin.ModelAdmin):
    list_display = ('name', 'private_ID', 'colony', 'is_alive', 'hp', 'max_hp', 'action', 'action_desc')

class ColonyAdmin(admin.ModelAdmin):
    list_display = ('name', 'player', 'game', 'food', 'ready')

class GameAdmin(admin.ModelAdmin):
    list_display = ('description', 'starting_torbs', 'round_number', 'private', 'closed', 'max_colonies_per_player')

class EvolutionEngineAdmin(admin.ModelAdmin):
    list_display = ('game', 'random_gene_min', 'random_gene_max', 'mutation_chance', 'mutation_dev', 'alleles_per_gene')

class ArmyAdmin(admin.ModelAdmin):
    list_display = ('colony', 'scout_target', 'attack_target', 'morale')

admin.site.register(Torb, TorbAdmin)
admin.site.register(Colony, ColonyAdmin)
admin.site.register(Game, GameAdmin)
admin.site.register(EvolutionEngine, EvolutionEngineAdmin)
admin.site.register(Army, ArmyAdmin)
admin.site.register(StoryText)
admin.site.register(ArmyTorb)
admin.site.register(Player)