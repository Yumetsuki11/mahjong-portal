from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils.safestring import mark_safe

from online.models import TournamentStatus, TournamentPlayers, TournamentGame, TournamentGamePlayer
from player.models import Player
from tournament.models import Tournament, OnlineTournamentRegistration


class TournamentGameForm(forms.ModelForm):

    class Meta:
        model = TournamentGame
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['tournament'].queryset = Tournament.objects.filter(tournament_type=Tournament.ONLINE)


class TournamentPlayersForm(forms.ModelForm):

    class Meta:
        model = TournamentPlayers
        exclude = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['tournament'].queryset = Tournament.objects.filter(tournament_type=Tournament.ONLINE).order_by('-start_date')


class TournamentStatusAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'current_round', 'end_break_time']


class TournamentPlayersAdmin(admin.ModelAdmin):
    form = TournamentPlayersForm
    list_display = ['tournament', 'player', 'telegram_username', 'tenhou_username', 'pantheon_id', 'add_to_pantheon_action']
    list_filter = [
        ['tournament', admin.RelatedOnlyFieldListFilter],
    ]

    def player(self, obj):
        if obj.pantheon_id:
            try:
                return Player.objects.get(pantheon_id=obj.pantheon_id)
            except Player.DoesNotExist:
                pass

        try:
            registration = OnlineTournamentRegistration.objects.filter(tenhou_nickname=obj.tenhou_username).last()
            if registration.player:
                return registration.player
        except:
            pass

        result = OnlineTournamentRegistration.objects.filter(tenhou_nickname=obj.tenhou_username).last()
        if result:
            return u'[{} {}]'.format(result.last_name, result.first_name)

        return None

    def add_to_pantheon_action(self, obj):
        if not obj.pantheon_id:
            return 'MISSED PANTHEON ID'

        if not obj.added_to_pantheon:
            url = reverse('add_user_to_the_pantheon', kwargs={'record_id': obj.id})
            return mark_safe('<a href="{}" class="button">Add to pantheon</a>'.format(url))

        return 'Added'


class TournamentGameAdmin(admin.ModelAdmin):
    form = TournamentGameForm
    list_display = ['tournament', 'tournament_round', 'status', 'log_id', 'created_on', 'updated_on']
    list_filter = [['tournament', admin.RelatedOnlyFieldListFilter], 'status', 'tournament_round',]


class TournamentGamePlayerAdmin(admin.ModelAdmin):
    list_display = ['player', 'game', 'wind', 'is_active']
    list_filter = [['game__tournament', admin.RelatedOnlyFieldListFilter], 'game__status']


admin.site.register(TournamentStatus, TournamentStatusAdmin)
admin.site.register(TournamentPlayers, TournamentPlayersAdmin)
admin.site.register(TournamentGame, TournamentGameAdmin)
admin.site.register(TournamentGamePlayer, TournamentGamePlayerAdmin)
