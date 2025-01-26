# Generated by Django 5.1 on 2024-08-24 02:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_game', '0002_colony_torb'),
    ]

    operations = [
        migrations.AddField(
            model_name='colony',
            name='name',
            field=models.CharField(default='DefaultName', max_length=64),
        ),
        migrations.AddField(
            model_name='colony',
            name='num_torbs',
            field=models.IntegerField(default=0),
        ),
    ]
