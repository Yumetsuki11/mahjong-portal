from django.contrib import admin

from online.models import TournamentStatus, TournamentPlayers, TournamentGame, TournamentGamePlayer


class TournamentStatusAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'current_round', 'end_break_time']


class TournamentPlayersAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'telegram_username', 'tenhou_username', 'pantheon_id']


class TournamentGameAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'tournament_round', 'status', 'log_id']


class TournamentGamePlayerAdmin(admin.ModelAdmin):
    list_display = ['player', 'game', 'wind', 'is_active']
    list_filter = ['game__status']


admin.site.register(TournamentStatus, TournamentStatusAdmin)
admin.site.register(TournamentPlayers, TournamentPlayersAdmin)
admin.site.register(TournamentGame, TournamentGameAdmin)
admin.site.register(TournamentGamePlayer, TournamentGamePlayerAdmin)
