# Generated by Django 5.1 on 2024-10-20 19:38

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_game', '0042_game_max_colonies_per_player'),
    ]

    operations = [
        migrations.AddField(
            model_name='storytext',
            name='game_round',
            field=models.IntegerField(default=-1),
        ),
        migrations.AddField(
            model_name='storytext',
            name='is_new',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='storytext',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
