# Generated by Django 3.2.10 on 2022-02-10 05:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('league', '0012_auto_20220210_0508'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='leaguegameplayer',
            name='player_pantheon_id',
        ),
        migrations.AddField(
            model_name='leaguegameplayer',
            name='player',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='games', to='league.leagueplayer'),
        ),
    ]
