# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2019-02-22 13:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_user_is_tournament_manager'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_ema_players_manager',
            field=models.BooleanField(default=False),
        ),
    ]
