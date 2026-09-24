"""API minima para el mod FluxLab Tracker (via el programa de escritorio).

POST /api/sesiones/
Authorization: Token <clave del perfil>
{"started_at": 1790213054, "ended_at": 1790213165, "flux_start": 493846544,
 "flux_end": 493846794, "activity": "delves" (opcional), "trove_class": "..." (opcional),
 "power_rank": 42000 (opcional)}
"""
import json
from datetime import datetime, timedelta, timezone as dt_timezone

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import CLASS_CHOICES, Activity, FarmSession, Profile

MAX_SESSION = timedelta(hours=24)
VALID_CLASSES = {c for c, _ in CLASS_CHOICES}


def _error(msg, status=400):
    return JsonResponse({"error": msg}, status=status)


def _user_from_request(request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Token "):
        return None
    key = auth[6:].strip()
    if not key:
        return None
    profile = Profile.objects.filter(api_key_hash=Profile.hash_key(key)).select_related("user").first()
    return profile.user if profile and profile.user.is_active else None


@csrf_exempt
@require_POST
def sessions(request):
    user = _user_from_request(request)
    if user is None:
        return _error("clave invalida", 401)
    try:
        data = json.loads(request.body or b"{}")
        started_ts = int(data["started_at"])
        ended_ts = int(data["ended_at"])
        flux_start = int(data["flux_start"])
        flux_end = int(data["flux_end"])
    except (ValueError, KeyError, TypeError):
        return _error("faltan started_at, ended_at, flux_start o flux_end")

    try:
        started = datetime.fromtimestamp(started_ts, tz=dt_timezone.utc)
        ended = datetime.fromtimestamp(ended_ts, tz=dt_timezone.utc)
    except (OverflowError, OSError, ValueError):
        return _error("fecha invalida")
    if ended <= started or ended - started > MAX_SESSION:
        return _error("la sesion debe durar entre 1 segundo y 24 horas")
    if ended > timezone.now() + timedelta(minutes=5):
        return _error("la sesion termina en el futuro")
    if flux_start < 0 or flux_end < 0:
        return _error("flux invalido")

    activity = None
    if data.get("activity"):
        activity = Activity.objects.filter(slug=str(data["activity"]), is_active=True).first()
    trove_class = str(data.get("trove_class") or "")
    if trove_class not in VALID_CLASSES:
        trove_class = ""
    try:
        power_rank = int(data["power_rank"]) if data.get("power_rank") else None
    except (TypeError, ValueError):
        power_rank = None
    if trove_class == "" and hasattr(user, "profile"):
        trove_class = user.profile.main_class

    session, created = FarmSession.objects.get_or_create(
        user=user,
        external_id=f"mod:{started_ts}",
        defaults={
            "source": "mod",
            "started_at": started,
            "ended_at": ended,
            # Si gastaste flux durante la sesion el total baja: se cuenta como 0.
            "flux": max(flux_end - flux_start, 0),
            "activity": activity,
            "trove_class": trove_class,
            "power_rank": power_rank,
            "is_logged": True,
        },
    )
    return JsonResponse({
        "id": session.pk,
        "created": created,
        "flux": session.flux,
        "minutes": round(session.hours * 60, 1),
        "flux_per_hour": session.flux_per_hour,
        "url": request.build_absolute_uri(session.get_absolute_url()),
    }, status=201 if created else 200)
