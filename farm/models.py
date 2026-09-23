from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _

# Las clases jugables de Trove (nombres oficiales, iguales en los dos idiomas).
TROVE_CLASSES = [
    "Bard", "Boomeranger", "Candy Barbarian", "Chloromancer", "Dino Tamer", "Dracolyte",
    "Fae Trickster", "Gunslinger", "Ice Sage", "Knight", "Lunar Lancer", "Neon Ninja",
    "Pirate Captain", "Revenant", "Shadow Hunter", "Solarion", "Tomb Raiser", "Vanguardian",
]
CLASS_CHOICES = [(c, c) for c in TROVE_CLASSES]

# Duracion minima para que una sesion cuente en el flux por hora.
MIN_RATED_MINUTES = 5


class Activity(models.Model):
    """Una forma de farmear: Delves, Geode, Shadow Tower, Ships... Se administra
    desde el admin para agregar las nuevas sin tocar codigo."""
    slug = models.SlugField(unique=True)
    name = models.CharField(_("nombre"), max_length=60)
    name_en = models.CharField(_("nombre en inglés"), max_length=60)
    order = models.PositiveSmallIntegerField(_("orden"), default=0)
    is_active = models.BooleanField(_("activa"), default=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = _("actividad")
        verbose_name_plural = _("actividades")

    def __str__(self):
        return self.display_name

    @property
    def display_name(self):
        return self.name_en if (get_language() or "es")[:2] == "en" else self.name


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    trove_name = models.CharField(_("nombre en Trove"), max_length=40, blank=True)
    main_class = models.CharField(_("clase principal"), max_length=30, choices=CLASS_CHOICES, blank=True)

    def __str__(self):
        return self.trove_name or self.user.username


class FarmSessionQuerySet(models.QuerySet):
    def logged(self):
        """Sesiones terminadas y con resultados registrados (las que cuentan en las estadísticas)."""
        return self.filter(ended_at__isnull=False, is_logged=True)

    def running(self):
        return self.filter(ended_at__isnull=True)


class FarmSession(models.Model):
    """Una sesion de farmeo. Mientras ended_at esta vacio, el cronometro corre."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="farm_sessions")
    activity = models.ForeignKey(
        Activity, on_delete=models.PROTECT, null=True, blank=True,
        related_name="sessions", verbose_name=_("actividad"),
    )
    trove_class = models.CharField(_("clase"), max_length=30, choices=CLASS_CHOICES, blank=True)
    power_rank = models.PositiveIntegerField(_("Power Rank"), null=True, blank=True)
    started_at = models.DateTimeField(_("inicio"), default=timezone.now)
    ended_at = models.DateTimeField(_("fin"), null=True, blank=True)
    flux = models.PositiveIntegerField(_("flux ganado"), default=0)
    cubits = models.PositiveIntegerField(_("cubits ganados"), default=0)
    notes = models.TextField(_("notas"), blank=True, max_length=1000)
    is_logged = models.BooleanField(default=False)
    share_with_community = models.BooleanField(_("contar en las estadísticas de la comunidad"), default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = FarmSessionQuerySet.as_manager()

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            # Solo un cronometro corriendo a la vez por jugador.
            models.UniqueConstraint(
                fields=["user"], condition=Q(ended_at__isnull=True), name="one_running_session_per_user"
            ),
        ]

    def __str__(self):
        return f"{self.user} · {self.activity or '—'} · {self.started_at:%Y-%m-%d}"

    def get_absolute_url(self):
        return reverse("farm:session_log", args=[self.pk])

    @property
    def is_running(self):
        return self.ended_at is None

    @property
    def duration(self):
        end = self.ended_at or timezone.now()
        return max(end - self.started_at, timedelta(0))

    @property
    def hours(self):
        return self.duration.total_seconds() / 3600

    @property
    def is_rated(self):
        """Solo las sesiones de al menos MIN_RATED_MINUTES cuentan para el flux/h:
        con unos segundos, cualquier flux da un ritmo absurdo."""
        return self.duration >= timedelta(minutes=MIN_RATED_MINUTES)

    @property
    def flux_per_hour(self):
        return round(self.flux / self.hours) if self.is_rated else None


class Goal(models.Model):
    """Meta de ahorro: 'Juntar 500.000 flux para X'. El progreso cuenta el flux
    de las sesiones registradas desde que se creo la meta."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="goals")
    name = models.CharField(_("meta"), max_length=80)
    target_flux = models.PositiveIntegerField(_("flux objetivo"))
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["completed_at", "-created_at"]

    def __str__(self):
        return self.name

    @property
    def earned(self):
        qs = self.user.farm_sessions.logged().filter(started_at__gte=self.created_at)
        if self.completed_at:
            qs = qs.filter(started_at__lte=self.completed_at)
        return qs.aggregate(total=Sum("flux"))["total"] or 0

    @property
    def remaining(self):
        return max(self.target_flux - self.earned, 0)

    @property
    def percent(self):
        return min(100, round(self.earned * 100 / self.target_flux)) if self.target_flux else 0
