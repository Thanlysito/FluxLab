"""Calculos de estadisticas de farmeo de un jugador."""
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import timedelta

from django.utils import timezone


@dataclass
class ActivityStats:
    activity: object
    sessions: int = 0
    hours: float = 0.0
    flux: int = 0
    # Solo sesiones de 5 min o mas, para el flux/h.
    rated_hours: float = 0.0
    rated_flux: int = 0

    @property
    def flux_per_hour(self):
        return round(self.rated_flux / self.rated_hours) if self.rated_hours > 0 else 0


@dataclass
class DayStats:
    date: object
    hours: float = 0.0
    flux: int = 0


@dataclass
class UserStats:
    sessions: int = 0
    hours: float = 0.0
    flux: int = 0
    cubits: int = 0
    by_activity: list = field(default_factory=list)
    last_7_days: list = field(default_factory=list)
    streak: int = 0
    rated_hours: float = 0.0
    rated_flux: int = 0

    @property
    def flux_per_hour(self):
        return round(self.rated_flux / self.rated_hours) if self.rated_hours > 0 else 0

    @property
    def best_activity(self):
        # Solo cuenta actividades con al menos 30 minutos registrados, para que
        # una sesion cortita con suerte no la gane.
        ranked = [a for a in self.by_activity if a.rated_hours >= 0.5]
        return max(ranked, key=lambda a: a.flux_per_hour, default=None)

    @property
    def max_day_flux(self):
        return max((d.flux for d in self.last_7_days), default=0)


def user_stats(user, since=None):
    qs = user.farm_sessions.logged().select_related("activity")
    if since is not None:
        qs = qs.filter(started_at__gte=since)
    sessions = list(qs)

    stats = UserStats()
    per_activity = {}
    per_day = defaultdict(lambda: [0.0, 0])
    today = timezone.localdate()

    for s in sessions:
        stats.sessions += 1
        stats.hours += s.hours
        stats.flux += s.flux
        stats.cubits += s.cubits
        rated = s.is_rated
        if rated:
            stats.rated_hours += s.hours
            stats.rated_flux += s.flux
        if s.activity_id:
            a = per_activity.setdefault(s.activity_id, ActivityStats(activity=s.activity))
            a.sessions += 1
            a.hours += s.hours
            a.flux += s.flux
            if rated:
                a.rated_hours += s.hours
                a.rated_flux += s.flux
        day = timezone.localtime(s.started_at).date()
        per_day[day][0] += s.hours
        per_day[day][1] += s.flux

    stats.by_activity = sorted(per_activity.values(), key=lambda a: a.flux_per_hour, reverse=True)
    # Racha: dias seguidos con farmeo, contando hasta hoy (o hasta ayer si hoy
    # todavia no ha farmeado).
    days = set(per_day)
    cursor = today if today in days else today - timedelta(days=1)
    while cursor in days:
        stats.streak += 1
        cursor -= timedelta(days=1)

    stats.last_7_days = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        hours, flux = per_day.get(d, (0.0, 0))
        stats.last_7_days.append(DayStats(date=d, hours=hours, flux=flux))
    return stats


def recent_flux_per_hour(user, days=30):
    """Ritmo reciente del jugador, para estimar cuanto le falta a una meta."""
    since = timezone.now() - timedelta(days=days)
    return user_stats(user, since=since).flux_per_hour
