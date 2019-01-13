import requests
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test, login_required
from django.http import HttpResponse
from django.shortcuts import redirect

from online.models import TournamentPlayers
from utils.general import make_random_letters_and_digit_string


@user_passes_test(lambda u: u.is_superuser)
@login_required
def add_user_to_the_pantheon(request, record_id):
    record = TournamentPlayers.objects.get(id=record_id)

    headers = {
        'X-Auth-Token': settings.PANTHEON_ADMIN_TOKEN,
    }

    # The first step is update player tenhou nickname
    data = {
        'jsonrpc': '2.0',
        'method': 'updatePlayer',
        'params': {
            'id': record.pantheon_id,
            'ident': '',
            'alias': '',
            'displayName': '',
            'tenhouId': record.tenhou_username
        },
        'id': make_random_letters_and_digit_string()
    }

    response = requests.post(settings.PANTHEON_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse('Update player. 500 response')

    content = response.json()
    if content.get('error'):
        return HttpResponse('Update player. Pantheon error: {}'.format(content.get('error')))

    # The second step is enroll player
    data = {
        'jsonrpc': '2.0',
        'method': 'enrollPlayerCP',
        'params': {
            'eventId': settings.PANTHEON_EVENT_ID,
            'playerId': record.pantheon_id,
        },
        'id': make_random_letters_and_digit_string()
    }

    response = requests.post(settings.PANTHEON_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse('Enroll player. 500 response')

    content = response.json()
    if content.get('error'):
        return HttpResponse('Enroll player. Pantheon error: {}'.format(content.get('error')))

    # The third step is register player
    data = {
        'jsonrpc': '2.0',
        'method': 'registerPlayerCP',
        'params': {
            'eventId': settings.PANTHEON_EVENT_ID,
            'playerId': record.pantheon_id,
        },
        'id': make_random_letters_and_digit_string()
    }

    response = requests.post(settings.PANTHEON_URL, json=data, headers=headers)
    if response.status_code == 500:
        return HttpResponse('Register player. 500 response')

    content = response.json()
    if content.get('error'):
        return HttpResponse('Register player. Pantheon error: {}'.format(content.get('error')))

    record.added_to_pantheon = True
    record.save()

    return redirect('admin:online_tournamentplayers_changelist')
