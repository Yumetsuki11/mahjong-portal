import csv
import io

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import translation
from django.utils.text import slugify
from django.utils.translation import get_language
from haystack.forms import ModelSearchForm

from club.models import Club
from player.models import Player, PlayerQuotaEvent
from player.tenhou.models import TenhouAggregatedStatistics
from rating.models import Rating, RatingResult
from rating.utils import get_latest_rating_date
from settings.models import City
from tournament.models import Tournament, TournamentResult


def home(request):
    rating = Rating.objects.get(type=Rating.RR)
    today, rating_date = get_latest_rating_date(rating)
    rating_results = (
        RatingResult.objects.filter(rating=rating)
        .filter(date=rating_date)
        .prefetch_related("player")
        .prefetch_related("player__city")
        .order_by("place")
    )[:16]

    upcoming_tournaments = (
        Tournament.public.filter(is_upcoming=True)
        .filter(is_event=False)
        .exclude(tournament_type=Tournament.FOREIGN_EMA)
        .prefetch_related("city")
        .order_by("start_date")
    )

    events = (
        Tournament.public.filter(is_upcoming=True).filter(is_event=True).prefetch_related("city").order_by("start_date")
    )

    return render(
        request,
        "website/home.html",
        {
            "page": "home",
            "rating_results": rating_results,
            "rating": rating,
            "upcoming_tournaments": upcoming_tournaments,
            "events": events,
            "rating_date": rating_date,
            "today": today,
            "is_last": True,
            "leagues": [],
        },
    )


def about(request):
    template = "about_en.html"
    if get_language() == "ru":
        template = "about_ru.html"

    return render(request, "website/{}".format(template), {"page": "about"})


def championships(request):
    championships = Tournament.objects.filter(
        Q(tournament_type=Tournament.CHAMPIONSHIP) | Q(russian_cup=True)
    ).order_by("-end_date")

    return render(request, "website/championships.html", {"championships": championships})


def contacts(request):
    template = "contacts_en.html"
    if get_language() == "ru":
        template = "contacts_ru.html"

    return render(request, "website/{}".format(template), {"page": "contacts"})


def search(request):
    query = request.GET.get("q", "")

    search_form = ModelSearchForm(request.GET, load_all=True)
    results = search_form.search()

    query_list = [x.object for x in results]
    players = [x for x in query_list if x.__class__ == Player]

    return render(request, "website/search.html", {"players": players, "search_query": query})


def city_page(request, slug):
    city = get_object_or_404(City, slug=slug)

    clubs = Club.objects.filter(city=city).prefetch_related("city")
    tournaments = Tournament.public.filter(city=city, is_event=False).order_by("-end_date").prefetch_related("city")

    players = Player.objects.filter(city=city).prefetch_related("city")
    for player in players:
        player.rank = -1

        tenhou_object = player.tenhou_object
        if tenhou_object:
            stat = tenhou_object.aggregated_statistics.filter(
                game_players=TenhouAggregatedStatistics.FOUR_PLAYERS
            ).first()

            player.rank = stat.rank
            player.rank_display = stat.get_rank_display()

    players = sorted(players, key=lambda x: (-x.rank, x.full_name))

    return render(
        request, "website/city.html", {"city": city, "clubs": clubs, "players": players, "tournaments": tournaments}
    )


def players_api(request):
    translation.activate("ru")

    players = (
        Player.objects.filter(country__code="RU").prefetch_related("city").prefetch_related("tenhou").order_by("id")
    )

    data = []
    for player in players:
        tenhou_query = player.tenhou.filter(is_main=True).first()
        tenhou_data = None
        if tenhou_query:
            tenhou_data = {
                "username": tenhou_query.tenhou_username,
                "rank": tenhou_query.get_rank_display(),
                "date": tenhou_query.username_created_at.strftime("%Y-%m-%d"),
            }

        data.append(
            {
                "id": player.id,
                "name": player.full_name,
                "city": player.city and player.city.name or "",
                "ema_id": player.ema_id or "",
                "tenhou": tenhou_data,
            }
        )
    return JsonResponse(data, safe=False)


def online_tournament_rules(request):
    template = "rules_en.html"
    if get_language() == "ru":
        template = "rules_ru.html"

    return render(request, "website/{}".format(template))


def rating_faq(request):
    template = "rating_faq_en.html"
    if get_language() == "ru":
        template = "rating_faq_ru.html"

    return render(request, "website/{}".format(template))


def iormc_2018(request):
    spring_id = 294
    summer_id = 310
    winter_id = 323

    tournament_ids = [spring_id, summer_id, winter_id]
    results = TournamentResult.objects.filter(tournament_id__in=tournament_ids).prefetch_related("player")
    data = {}
    for result in results:
        if result.player.is_hide or result.player.is_replacement:
            continue

        if not data.get(result.player_id):
            data[result.player_id] = {
                "player": result.player,
                "first": 0,
                "second": 0,
                "third": 0,
                "total": 0,
                "number_of_played": 0,
            }

        if result.tournament_id == spring_id:
            data[result.player_id]["first"] = result.scores
            data[result.player_id]["number_of_played"] += 1

        if result.tournament_id == summer_id:
            data[result.player_id]["second"] = result.scores
            data[result.player_id]["number_of_played"] += 1

        if result.tournament_id == winter_id:
            data[result.player_id]["third"] = result.scores
            data[result.player_id]["number_of_played"] += 1

    for key, value in data.items():
        if data[key]["number_of_played"] <= 2:
            data[key]["total"] = value["first"] + value["second"] + value["third"]
        else:
            first = value["first"] + value["second"]
            second = value["first"] + value["third"]
            third = value["second"] + value["third"]

            data[key]["total"] = max([first, second, third])

    data = sorted(data.values(), key=lambda x: (x["number_of_played"] >= 2, x["total"]), reverse=True)

    return render(request, "website/iormc.html", {"data": data})


def ermc_qualification_2019(request):
    return qualification_view(request, PlayerQuotaEvent.ERMC_2019, "website/erc_2019.html")


def wrc_qualification_2020(request):
    return qualification_view(request, PlayerQuotaEvent.WRC_2020, "website/wrc_2020.html")


def qualification_view(request, q_type, template):
    results = PlayerQuotaEvent.objects.filter(type=q_type)
    confirmed = 1
    not_confirmed_colors = [
        PlayerQuotaEvent.GRAY,
        PlayerQuotaEvent.DARK_GREEN,
        PlayerQuotaEvent.DARK_BLUE,
        PlayerQuotaEvent.NEW,
    ]
    for x in results:
        if x.state in not_confirmed_colors:
            x.confirmed = None
        else:
            x.confirmed = confirmed
            confirmed += 1

    return render(request, template, {"rating_results": results})


@user_passes_test(lambda u: u.is_superuser)
@login_required
def export_tournament_results(request, tournament_id):
    content = io.StringIO()
    writer = csv.writer(content)

    rows = [
        [
            "Tournament name",
            "Number of participants",
            "Place",
            "Player's first name",
            "Player's last name",
            "EMA number",
            "Table points",
            "Score",
            "EMA member",
            "Country",
            "Date",
            "Countrycourt",
            "city",
            "mers",
            "shortname",
            "rules",
            "period",
            "NbDays",
            "Extra",
        ]
    ]

    tournament = Tournament.objects.get(id=tournament_id)

    for result in tournament.results.all().order_by("place"):
        player = Player.objects.get(id=result.player_id)

        rows.append(
            [
                "{} {}".format(tournament.name_en, tournament.end_date.year),
                tournament.number_of_players,
                result.place,
                player.first_name_en,
                player.last_name_en.upper(),
                player.ema_id or "",
                "1",
                result.scores,
                player.ema_id and "YES" or "",
                player.country and player.country.name_en == "Russia" and "RUS" or "",
                tournament.end_date.strftime("%d.%m.%Y"),
                "RUS",
                tournament.city.name_en,
                "",
                "",
                "Riichi",
                "",
                "",
                "NO",
            ]
        )

    for x in rows:
        writer.writerow(x)

    file_name = slugify("{} {} results".format(tournament.name_en, tournament.end_date.year))

    response = HttpResponse(content.getvalue(), content_type="text/plain")
    response["Content-Disposition"] = "attachment; filename={}.csv".format(file_name)
    return response
