import logging

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import ArmyActionForm, ColonyActionForm, LabActionForm
from .models import Colony, Discovery, Game, StoryText
from .selectors.access import get_owned_colony
from .services.actions import ActionService
from .services.colony_creation import ColonyService

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def colony_view(request, colony_id):
    colony = get_owned_colony(request.user, colony_id)
    torbs = colony.torbs.all().order_by("private_ID")
    if request.method == "POST":
        data = request.POST.copy()
        data["player_action"] = data.get("player-action")
        form = ColonyActionForm(data, torbs=torbs)
        if form.is_valid():
            action = form.cleaned_data["player_action"]
            kwargs = {}
            if action != "end_turn":
                kwargs["torb_ids"] = form.cleaned_data["selected_torbs"]
            try:
                ActionService.perform(
                    player=colony.player,
                    colony=colony,
                    action=action,
                    **kwargs,
                )
            except ValueError as error:
                messages.error(request, str(error))
            else:
                messages.success(request, "Colony action updated.")
        else:
            messages.error(request, "Invalid colony action.")
        return redirect("colony_view", colony_id=colony.pk)

    gene_names = list(torbs.first().genes) if torbs.exists() else []
    unique_actions = sorted(
        {action.capitalize() for action in torbs.values_list("action", flat=True)}
    )
    return render(
        request,
        "main_game/colony.html",
        {
            "colony": colony,
            "num_torbs": colony.torb_count,
            "torbs": torbs,
            "gene_names": gene_names,
            "story_texts": StoryText.objects.filter(colony=colony).order_by("timestamp"),
            "unique_actions": unique_actions,
        },
    )


@login_required
@require_GET
def check_ready_status(request, colony_id):
    colony = get_owned_colony(request.user, colony_id)
    return JsonResponse({"ready": colony.ready})


@login_required
@require_http_methods(["GET", "POST"])
def play(request):
    error_message = None
    if request.method == "POST":
        try:
            ColonyService.join_game(
                game_id=request.POST.get("game_id"),
                user=request.user,
                name=request.POST.get("colony_name") or "DefaultName",
            )
        except (Game.DoesNotExist, PermissionError, ValueError) as error:
            error_message = str(error)
            messages.error(request, error_message)
        else:
            messages.success(request, "Colony created.")
            return redirect("play")

    games = Game.objects.filter(private=False) | Game.objects.filter(allowed_players=request.user)
    return render(
        request,
        "main_game/load_colony.html",
        {
            "colonies": Colony.objects.filter(player__user=request.user),
            "games": games.distinct(),
            "error_message": error_message,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def army_view(request, colony_id):
    colony = get_owned_colony(request.user, colony_id)
    if request.method == "POST":
        data = request.POST.copy()
        data["player_action"] = data.get("player-action")
        form = ArmyActionForm(data)
        if form.is_valid():
            try:
                ActionService.perform(
                    player=colony.player,
                    colony=colony,
                    action=form.cleaned_data["player_action"],
                    target_colony_id=form.cleaned_data["selected_colony"],
                )
            except (Colony.DoesNotExist, ValueError) as error:
                logger.info("Rejected army action: %s", error)
                messages.error(request, str(error))
            else:
                messages.success(request, "Army orders updated.")
        else:
            messages.error(request, "Invalid army action.")
        return redirect("army_view", colony_id=colony.pk)

    torbs = colony.torbs.all()
    return render(
        request,
        "main_game/army.html",
        {
            "colony": colony,
            "player_colony": colony,
            "story_texts": StoryText.objects.filter(colony=colony).order_by("timestamp"),
            "num_soldiers": torbs.filter(action="soldiering").count(),
            "num_training": torbs.filter(action="training").count(),
            "known_colonies": colony.discovered_colonies.order_by("pk"),
            "all_colonies": colony.game.colony_set.order_by("pk"),
        },
    )


@login_required
@require_GET
def settings_view(request, colony_id):
    colony = get_owned_colony(request.user, colony_id)
    return render(request, "main_game/settings.html", {"colony": colony})


@login_required
@require_http_methods(["GET", "POST"])
def lab_view(request, colony_id):
    colony = get_owned_colony(request.user, colony_id)
    torbs = colony.torbs.all().order_by("private_ID")
    error_message = None
    if request.method == "POST":
        data = request.POST.copy()
        data["player_action"] = data.get("player-action")
        form = LabActionForm(data, torbs=torbs)
        if form.is_valid():
            action = form.cleaned_data["player_action"]
            kwargs = {}
            if action == "research":
                kwargs["torb_ids"] = form.cleaned_data["selected_torbs"]
            elif action == "make_mutagen":
                kwargs["science_points_used"] = form.cleaned_data["science_points_used"]
            elif action == "purchase_discovery":
                kwargs["discovery_id"] = form.cleaned_data["discovery_id"]
            try:
                ActionService.perform(player=colony.player, colony=colony, action=action, **kwargs)
            except (TypeError, ValueError, Discovery.DoesNotExist) as error:
                error_message = str(error)
                messages.error(request, error_message)
            else:
                messages.success(request, "Lab action completed.")
                return redirect("lab_view", colony_id=colony.pk)
        else:
            error_message = "Invalid lab action."
            messages.error(request, error_message)

    unlocked = colony.lab.discoveries.order_by("research_cost", "name")
    return render(
        request,
        "main_game/lab.html",
        {
            "colony": colony,
            "torbs": torbs,
            "unlocked_discoveries": unlocked,
            "available_discoveries": Discovery.objects.exclude(pk__in=unlocked).order_by(
                "research_cost", "name"
            ),
            "error_message": error_message,
        },
    )


@require_GET
def main_page(request):
    if request.user.is_authenticated:
        return redirect("play")
    return render(request, "main_game/main_page.html")


class RegisterForm(UserCreationForm):
    usable_password = None

    class Meta:
        model = get_user_model()
        fields = ["username", "password1", "password2"]


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("play")
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        user = authenticate(
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password1"],
        )
        login(request, user)
        messages.success(request, "Registration complete.")
        return redirect("play")
    return render(request, "main_game/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("play")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Logged in.")
        return redirect("play")
    return render(request, "main_game/login.html", {"form": form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out.")
    return redirect("main_page")


@login_required
@require_GET
def filter_torbs(request, colony_id):
    colony = get_owned_colony(request.user, colony_id)
    torbs = colony.torbs.all()
    action_filter = request.GET.get("action", "all")
    fertile_filter = request.GET.get("fertile", "all")
    if action_filter != "all":
        torbs = torbs.filter(action__in=action_filter.lower().split(","))
    if fertile_filter in {"fertile", "infertile"}:
        torbs = torbs.filter(fertile=fertile_filter == "fertile")
    torbs = torbs.order_by("private_ID")
    gene_names = list(torbs.first().genes) if torbs.exists() else []
    return JsonResponse(
        {
            "torbs": [
                {
                    "id": torb.pk,
                    "private_ID": torb.private_ID,
                    "generation": torb.generation,
                    "name": torb.name,
                    "hp": torb.hp,
                    "max_hp": torb.max_hp,
                    "action": torb.action.capitalize(),
                    "action_desc": torb.action_desc,
                    "genes": {
                        gene: [f"{allele:.1f}" for allele in alleles]
                        for gene, alleles in torb.genes.items()
                    },
                    "status": torb.status,
                    "fertile": torb.fertile,
                }
                for torb in torbs
            ],
            "gene_names": gene_names,
        }
    )
