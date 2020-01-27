# Generated by Django 2.2.6 on 2020-01-27 05:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('player', '0008_auto_20191218_1440'),
    ]

    operations = [
        migrations.CreateModel(
            name='PlayerWRC',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('updated_on', models.DateTimeField(auto_now=True)),
                ('state', models.PositiveSmallIntegerField(choices=[[0, 'точно едет'], [1, 'скорее всего едет'], [2, 'пока сомневается, но скорее всего не едет'], [3, 'игрок пока ничего не ответил'], [4, 'игрок пока что не проходит, но готов ехать, если появится квота'], [5, 'точно не едет'], [6, 'чемпион европы'], [7, 'игрок замены'], [8, 'не деда (судья)']])),
                ('federation_member', models.BooleanField(default=False)),
                ('player', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='wrc', to='player.Player')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
