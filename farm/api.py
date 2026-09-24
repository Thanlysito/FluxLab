"""API minima para el mod FluxLab Tracker (via el programa de escritorio).

POST /api/sesiones/
Authorization: Token <clave del perfil>
{"started_at": 1790213054, "ended_at": 1790213165, "flux_start": 493846544,
 "flux_end": 493846794, "activity": "delves" (opcional), "trove_class": "..." (opcional),
 "power_rank": 42000 (opcional),
 "loot": [{"key": "a:Mega Dark (13) Gem Box", "name": "Mega Dark (13) Gem Box", "qty": 3}] (opcional)}
"""
import json
from datetime import datetime, timedelta, timezone as dt_timezone

from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import CLASS_CHOICES, Activity, FarmSession, LootItem, Profile

MAX_SESSION = timedelta(hours=24)
MAX_LOOT_ITEMS = 400
VALID_CLASSES = {c for c, _ in CLASS_CHOICES}
CLASS_BY_LOWER = {c.lower(): c for c in VALID_CLASSES}


def _error(msg, status=400):
    return JsonResponse({"error": msg}, status=status)


def _clean_loot(raw):
    """Lista de objetos ganados, limpia. Lo que venga raro se ignora."""
    items = {}
    if not isinstance(raw, list):
        return items
    for it in raw[:MAX_LOOT_ITEMS]:
        if not isinstance(it, dict):
            continue
        try:
            qty = int(it.get("qty"))
        except (TypeError, ValueError):
            continue
        key = str(it.get("key") or "")[:160].strip()
        name = str(it.get("name") or "")[:120].strip()
        if key and name and 0 < qty <= 2_000_000_000:
            items[key] = (name, qty)
    return items


# Objetos que solo salen en una actividad: si la sesion los trae, esa es la actividad.
ACTIVITY_HINTS = [
    ("c:item/crafting/delvekey", "delves"),
]


def _guess_activity(loot):
    for prefix, slug in ACTIVITY_HINTS:
        if any(k.startswith(prefix) for k in loot):
            return Activity.objects.filter(slug=slug, is_active=True).first()
    return None


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
    # El HUD manda el nombre tal como lo muestra el juego: se compara sin mayusculas.
    raw_class = " ".join(str(data.get("trove_class") or "").split()).lower()
    trove_class = CLASS_BY_LOWER.get(raw_class, "")
    try:
        power_rank = int(data["power_rank"]) if data.get("power_rank") else None
    except (TypeError, ValueError):
        power_rank = None
    if trove_class == "" and hasattr(user, "profile"):
        trove_class = user.profile.main_class

    loot = _clean_loot(data.get("loot"))
    if activity is None:
        activity = _guess_activity(loot)

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
    # Una sesion que llego sin objetos (companion viejo, foto incompleta) los puede
    # recibir despues; si ya los tiene no se tocan.
    if loot and not session.loot.exists():
        LootItem.objects.bulk_create(
            [LootItem(session=session, key=k, name=n, quantity=q) for k, (n, q) in loot.items()]
        )
    return JsonResponse({
        "id": session.pk,
        "loot_items": session.loot.count(),
        "created": created,
        "flux": session.flux,
        "minutes": round(session.hours * 60, 1),
        "flux_per_hour": session.flux_per_hour,
        "url": request.build_absolute_uri(session.get_absolute_url()),
    }, status=201 if created else 200)
