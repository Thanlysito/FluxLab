"""Lo farmeado aparte del flux (materiales, cajas de gemas, objetos), agrupado."""
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from .models import LootItem

GROUPS = [
    ("gems", _("Cajas de gemas")),
    ("materials", _("Monedas y materiales")),
    ("items", _("Objetos")),
]


def group_of(key, name):
    if "gem box" in name.lower():
        return "gems"
    if key.startswith("c:"):
        return "materials"
    return "items"


def grouped(rows):
    """rows: iterable de (key, name, quantity[, per_hour]) -> [(titulo, [fila, ...]), ...]."""
    buckets = {g: [] for g, _t in GROUPS}
    for row in rows:
        buckets[group_of(row["key"], row["name"])].append(row)
    return [(title, buckets[g]) for g, title in GROUPS if buckets[g]]


def session_loot(session):
    return grouped(
        {"key": i.key, "name": i.name, "quantity": i.quantity} for i in session.loot.all()
    )


def loot_totals(user, since=None, limit=15):
    """Totales de lo farmeado en el periodo, con cuanto sale por hora.

    El 'por hora' solo usa las sesiones que traen objetos (las del mod con foto del
    inventario) y que duran lo suficiente para contar."""
    sessions = user.farm_sessions.logged().filter(loot__isnull=False).distinct()
    if since is not None:
        sessions = sessions.filter(started_at__gte=since)
    sessions = list(sessions)
    if not sessions:
        return None
    hours = sum(s.hours for s in sessions if s.is_rated)
    rows = (
        LootItem.objects.filter(session__in=sessions)
        .values("key", "name").annotate(quantity=Sum("quantity")).order_by("-quantity", "name")
    )
    rows = [
        {**r, "per_hour": round(r["quantity"] / hours, 1) if hours else None}
        for r in rows
    ]
    groups = []
    for title, items in grouped(rows):
        groups.append((title, items[:limit], len(items) - min(len(items), limit)))
    return {"sessions": len(sessions), "hours": hours, "groups": groups}
