# Generated by Django 5.1 on 2024-08-24 03:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_game', '0004_remove_colony_num_torbs_torb_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('starting_torbs', models.IntegerField(default=4)),
            ],
        ),
        migrations.AddField(
            model_name='colony',
            name='game',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='main_game.game'),
            preserve_default=False,
        ),
    ]
