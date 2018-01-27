from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language

from club.club_games.models import ClubSession
from club.models import Club


def club_list(request):
    clubs = Club.objects.all().order_by('city__name').prefetch_related('city')

    map_language = 'en_US'
    if get_language() == 'ru':
        map_language = 'ru_RU'

    return render(request, 'club/list.html', {
        'clubs': clubs,
        'map_language': map_language,
        'page': 'club'
    })


def club_details(request, slug):
    club = get_object_or_404(Club, slug=slug)
    tournaments = club.tournament_set.all().order_by('-end_date').prefetch_related('city')

    club_sessions = (club.club_sessions
                     .all()
                     .order_by('-date')
                     .prefetch_related('results')
                     .prefetch_related('results__player')
                     )[:10]
    total_sessions = club.club_sessions.all().count()

    default_sort = 'avg'
    sort = request.GET.get('sort', default_sort)
    sorting = {
        'avg': 'average_place',
        'ippatsu': '-ippatsu_chance',
        'dora': '-average_dora_in_hand',
        'ron': 'feed_percentage',
    }
    sort = sorting.get(sort, 'average_place')

    club_rating = (club.rating
                   .filter(games_count__gte=5)
                   .order_by(sort)
                   .prefetch_related('player'))

    return render(request, 'club/details.html', {
        'club': club,
        'tournaments': tournaments,
        'page': 'club',
        'club_sessions': club_sessions,
        'club_rating': club_rating,
        'total_sessions': total_sessions
    })
