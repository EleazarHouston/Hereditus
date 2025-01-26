# Generated by Django 5.1 on 2024-08-25 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_game', '0017_torb_genes'),
    ]

    operations = [
        migrations.AddField(
            model_name='torb',
            name='action',
            field=models.CharField(choices=[('gathering', 'gathering'), ('breeding', 'breeding'), ('combatting', 'combatting'), ('training', 'training'), ('resting', 'resting')], default='gathering', max_length=32),
        ),
        migrations.AddField(
            model_name='torb',
            name='action_desc',
            field=models.CharField(default='Gathering', max_length=256),
        ),
    ]
