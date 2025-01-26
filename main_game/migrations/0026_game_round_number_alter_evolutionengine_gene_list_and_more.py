# Generated by Django 5.1 on 2024-08-26 02:14

import django.db.models.deletion
import main_game.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_game', '0025_colony_gather_rate_colony_rest_heal_flat_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='round_number',
            field=models.IntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='evolutionengine',
            name='gene_list',
            field=models.JSONField(default=main_game.models.evolution_engine.default_gene_list),
        ),
        migrations.AlterField(
            model_name='game',
            name='evolution_engine',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='game_instance', to='main_game.evolutionengine'),
        ),
    ]
