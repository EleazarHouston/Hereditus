# Generated by Django 5.1 on 2024-08-25 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_game', '0022_storytext'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storytext',
            name='timestamp',
            field=models.DateTimeField(),
        ),
    ]
