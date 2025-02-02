import requests
from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from online.handler import TournamentHandler
from online.models import TournamentGame, TournamentNotification, TournamentPlayers
from tournament.models import Tournament
from utils.general import make_random_letters_and_digit_string
from utils.pantheon import add_user_to_pantheon


@user_passes_test(lambda u: u.is_superuser)
@login_required
def add_user_to_the_pantheon(request, record_id):
    record = TournamentPlayers.objects.get(id=record_id)
    add_user_to_pantheon(record)
    return redirect(request.META.get("HTTP_REFERER"))


@user_passes_test(lambda u: u.is_superuser)
@login_required
def disable_user_in_pantheon(request, record_id):
    record = TournamentPlayers.objects.get(id=record_id)

    headers = {"X-Auth-Token": settings.PANTHEON_ADMIN_TOKEN}

    data = {
        "jsonrpc": "2.0",
        "method": "updatePlayerSeatingFlagCP",
        "params": {
            "playerId": record.pantheon_id,
            "eventId": settings.PANTHEON_TOURNAMENT_EVENT_ID,
            "ignoreSeating": 1,
        },
        "id": make_random_letters_and_digit_string(),
    }

    response = requests.post(settings.PANTHEON_OLD_API_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse("Disable player. 500 response")

    content = response.json()
    if content.get("error"):
        return HttpResponse("Disable player. Pantheon error: {}".format(content.get("error")))

    record.enabled_in_pantheon = False
    record.save()

    return redirect(request.META.get("HTTP_REFERER"))


@user_passes_test(lambda u: u.is_superuser)
@login_required
def toggle_replacement_flag_in_pantheon(request, record_id):
    record = TournamentPlayers.objects.get(id=record_id)

    headers = {"X-Auth-Token": settings.PANTHEON_ADMIN_TOKEN}

    new_is_replacement = not record.is_replacement

    data = {
        "jsonrpc": "2.0",
        "method": "updatePlayer",
        "params": {
            "id": record.pantheon_id,
            "ident": "",
            "alias": "",
            "displayName": "",
            "tenhouId": record.tenhou_username,
            "isReplacement": new_is_replacement,
        },
        "id": make_random_letters_and_digit_string(),
    }

    response = requests.post(settings.PANTHEON_OLD_API_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse("updatePlayer. 500 response")

    content = response.json()
    if content.get("error"):
        return HttpResponse("updatePlayer. Pantheon error: {}".format(content.get("error")))

    record.is_replacement = new_is_replacement
    record.save()

    return redirect(request.META.get("HTTP_REFERER"))


@user_passes_test(lambda u: u.is_superuser)
@login_required
def add_penalty_game(request, game_id):
    game = TournamentGame.objects.get(id=game_id)

    headers = {"X-Auth-Token": settings.PANTHEON_ADMIN_TOKEN}
    data = {
        "jsonrpc": "2.0",
        "method": "addPenaltyGame",
        "params": {
            "eventId": settings.PANTHEON_TOURNAMENT_EVENT_ID,
            "players": [x.player.pantheon_id for x in game.game_players.all()],
        },
        "id": make_random_letters_and_digit_string(),
    }

    response = requests.post(settings.PANTHEON_OLD_API_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse("addPenaltyGame. 500 response")

    content = response.json()
    if content.get("error"):
        return HttpResponse("addPenaltyGame. Pantheon error: {}".format(content.get("error")))

    handler = TournamentHandler()
    handler.init(tournament=Tournament.objects.get(id=settings.TOURNAMENT_ID), lobby="", game_type="", destination="")
    player_names = handler.get_players_message_string([x.player for x in game.game_players.all()])
    handler.create_notification(TournamentNotification.GAME_PENALTY, {"player_names": player_names})
    handler.check_round_was_finished()

    return redirect(request.META.get("HTTP_REFERER"))


@require_POST
@csrf_exempt
def finish_game_api(request):
    api_token = request.POST.get("api_token")
    if api_token != settings.TOURNAMENT_API_TOKEN:
        return HttpResponse(status=403)

    message = request.POST.get("message")

    handler = TournamentHandler()
    handler.init(tournament=Tournament.objects.get(id=settings.TOURNAMENT_ID), lobby="", game_type="", destination="")
    handler.game_pre_end(message)

    return JsonResponse({"success": True})
