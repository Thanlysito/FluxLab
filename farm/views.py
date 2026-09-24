from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from .loot import loot_totals, session_loot
from .forms import GoalForm, ManualSessionForm, ProfileForm, SessionResultForm, SignupForm
from .models import MIN_RATED_MINUTES, Activity, FarmSession, Goal, Profile
from .stats import recent_flux_per_hour, user_stats
from .templatetags.farm_extras import fnum


def _format_duration(td):
    minutes = int(td.total_seconds() // 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes:02d} min" if hours else f"{minutes} min"


def home(request):
    if not request.user.is_authenticated:
        return render(request, "farm/landing.html")

    user = request.user
    week = user_stats(user, since=timezone.now() - timedelta(days=7))
    pace = recent_flux_per_hour(user)
    goals = list(user.goals.filter(completed_at__isnull=True)[:3])
    for g in goals:
        g.eta_hours = round(g.remaining / pace, 1) if pace else None
    return render(request, "farm/home.html", {
        "week": week,
        "pace": pace,
        "goals": goals,
        "activities": Activity.objects.filter(is_active=True),
        "pending": user.farm_sessions.filter(ended_at__isnull=False, is_logged=False)[:3],
        "recent": user.farm_sessions.logged().select_related("activity")[:5],
    })


def signup(request):
    if request.user.is_authenticated:
        return redirect("farm:home")
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data["email"]
        user.save()
        Profile.objects.get_or_create(user=user)
        login(request, user)
        messages.success(request, _("¡Bienvenido a FluxLab! Dale a «Empezar» la próxima vez que farmees."))
        return redirect("farm:home")
    return render(request, "registration/signup.html", {"form": form})


# --- Cronometro -------------------------------------------------------------

@login_required
@require_POST
def session_start(request):
    if request.user.farm_sessions.running().exists():
        messages.info(request, _("Ya tienes un cronómetro corriendo."))
        return redirect("farm:home")
    activity = Activity.objects.filter(pk=request.POST.get("activity") or None, is_active=True).first()
    try:
        FarmSession.objects.create(user=request.user, activity=activity)
    except IntegrityError:  # doble clic: ya se creo una
        pass
    return redirect("farm:home")


@login_required
@require_POST
def session_stop(request):
    session = request.user.farm_sessions.running().first()
    if session is None:
        return redirect("farm:home")
    session.ended_at = timezone.now()
    session.save(update_fields=["ended_at"])
    return redirect("farm:session_log", pk=session.pk)


@login_required
def session_log(request, pk):
    """Anotar lo que ganaste en una sesion ya terminada (o corregirla despues)."""
    session = get_object_or_404(FarmSession, pk=pk, user=request.user)
    if session.is_running:
        return redirect("farm:home")
    if not session.trove_class or not session.power_rank:
        last = request.user.farm_sessions.logged().exclude(pk=session.pk).first()
        profile = getattr(request.user, "profile", None)
        initial = {
            "trove_class": session.trove_class or (last.trove_class if last else "")
            or (profile.main_class if profile else ""),
            "power_rank": session.power_rank or (last.power_rank if last else None),
        }
    else:
        initial = {}
    form = SessionResultForm(request.POST or None, instance=session, initial=initial)
    if request.method == "POST" and form.is_valid():
        session = form.save(commit=False)
        session.is_logged = True
        session.save()
        if session.is_rated:
            messages.success(request, _("Sesión guardada: %(flux)s flux en %(time)s (%(fph)s flux/h).") % {
                "flux": fnum(session.flux), "time": _format_duration(session.duration),
                "fph": fnum(session.flux_per_hour),
            })
        else:
            messages.success(request, _(
                "Sesión guardada: %(flux)s flux. Duró menos de %(min)s minutos, así que no cuenta para el flux por hora."
            ) % {"flux": fnum(session.flux), "min": MIN_RATED_MINUTES})
        return redirect("farm:home")
    return render(request, "farm/session_log.html", {
        "form": form, "session": session, "min_rated": MIN_RATED_MINUTES,
        "loot": session_loot(session),
    })


@login_required
def session_new(request):
    """Anotar una sesion que no se cronometro."""
    form = ManualSessionForm(request.POST or None, initial={
        "started_at": timezone.localtime().replace(second=0, microsecond=0) - timedelta(hours=1),
        "minutes": 60,
    })
    if request.method == "POST" and form.is_valid():
        session = form.save(commit=False)
        session.user = request.user
        session.save()
        messages.success(request, _("Sesión guardada."))
        return redirect("farm:home")
    return render(request, "farm/session_new.html", {"form": form})


@login_required
@require_POST
def session_delete(request, pk):
    session = get_object_or_404(FarmSession, pk=pk, user=request.user)
    session.delete()
    messages.success(request, _("Sesión eliminada."))
    return redirect(request.POST.get("next") or "farm:history")


@login_required
def history(request):
    qs = (request.user.farm_sessions.filter(ended_at__isnull=False).select_related("activity")
          .annotate(loot_count=Count("loot")).order_by("-started_at"))
    page = Paginator(qs, 20).get_page(request.GET.get("page"))
    return render(request, "farm/history.html", {"page_obj": page})


# --- Estadisticas y metas ----------------------------------------------------

PERIODS = {"7": 7, "30": 30, "all": None}


@login_required
def stats(request):
    period = request.GET.get("period", "30")
    days = PERIODS.get(period, 30)
    since = timezone.now() - timedelta(days=days) if days else None
    return render(request, "farm/stats.html", {
        "stats": user_stats(request.user, since=since),
        "loot": loot_totals(request.user, since=since),
        "period": period if period in PERIODS else "30",
    })


@login_required
def goals(request):
    form = GoalForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        goal = form.save(commit=False)
        goal.user = request.user
        goal.save()
        messages.success(request, _("Meta creada. El flux que registres desde ahora cuenta para ella."))
        return redirect("farm:goals")
    pace = recent_flux_per_hour(request.user)
    goal_list = list(request.user.goals.all())
    for g in goal_list:
        g.eta_hours = round(g.remaining / pace, 1) if pace and not g.completed_at else None
    return render(request, "farm/goals.html", {"form": form, "goals": goal_list, "pace": pace})


@login_required
@require_POST
def goal_complete(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    goal.completed_at = timezone.now()
    goal.save(update_fields=["completed_at"])
    messages.success(request, _("¡Meta cumplida! 🎉"))
    return redirect("farm:goals")


@login_required
@require_POST
def goal_delete(request, pk):
    get_object_or_404(Goal, pk=pk, user=request.user).delete()
    messages.success(request, _("Meta eliminada."))
    return redirect("farm:goals")


@login_required
@require_POST
def api_key(request):
    profile, _created = Profile.objects.get_or_create(user=request.user)
    request.session["new_api_key"] = profile.new_api_key()
    return redirect("farm:profile")


@login_required
def profile(request):
    obj, _created = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, _("Perfil actualizado."))
        return redirect("farm:profile")
    return render(request, "farm/profile.html", {
        "form": form,
        "has_api_key": bool(obj.api_key_hash),
        # La clave se muestra una sola vez, justo despues de generarla.
        "new_api_key": request.session.pop("new_api_key", None),
    })
