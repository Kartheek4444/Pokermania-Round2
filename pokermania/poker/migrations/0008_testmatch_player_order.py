# Generated by Django 5.1.5 on 2025-02-27 20:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('poker', '0007_testmatch_bot1_alter_testmatch_players'),
    ]

    operations = [
        migrations.AddField(
            model_name='testmatch',
            name='player_order',
            field=models.JSONField(default=list),
        ),
    ]
