from datetime import timedelta

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Activity, FarmSession, Goal, Profile


class NoColonMixin:
    """Etiquetas sin los dos puntos que Django pone por defecto."""
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)


class SignupForm(NoColonMixin, UserCreationForm):
    email = forms.EmailField(
        label=_("Correo"), required=True,
        help_text=_("Solo para recuperar tu contraseña."),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class ActivityChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.display_name


class SessionResultForm(forms.ModelForm):
    """Lo que se anota al terminar una sesion: menos de 30 segundos."""
    activity = ActivityChoiceField(
        label=_("Actividad"), queryset=Activity.objects.filter(is_active=True),
        empty_label=_("Elige la actividad"),
    )

    class Meta:
        model = FarmSession
        fields = ["activity", "flux", "cubits", "trove_class", "power_rank", "notes", "share_with_community"]
        labels = {
            "flux": _("Flux ganado"),
            "cubits": _("Cubits ganados"),
            "trove_class": _("Clase"),
            "power_rank": _("Power Rank"),
            "notes": _("Notas"),
            "share_with_community": _("Contar en las estadísticas de la comunidad (anónimo)"),
        }
        widgets = {
            "flux": forms.NumberInput(attrs={"inputmode": "numeric", "min": 0, "autofocus": True}),
            "cubits": forms.NumberInput(attrs={"inputmode": "numeric", "min": 0}),
            "power_rank": forms.NumberInput(attrs={"inputmode": "numeric", "min": 0}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)
        # Cubits es opcional: vacio cuenta como 0.
        self.fields["cubits"].required = False
        self.fields["cubits"].widget.attrs["placeholder"] = "0"

    def clean_cubits(self):
        return self.cleaned_data.get("cubits") or 0


class ManualSessionForm(SessionResultForm):
    """Para anotar una sesion que no se cronometro."""
    started_at = forms.DateTimeField(
        label=_("¿Cuándo empezaste?"),
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    minutes = forms.IntegerField(label=_("Duración (minutos)"), min_value=1, max_value=24 * 60)

    class Meta(SessionResultForm.Meta):
        fields = ["started_at", "minutes"] + SessionResultForm.Meta.fields

    def clean_started_at(self):
        started = self.cleaned_data["started_at"]
        if started > timezone.now():
            raise forms.ValidationError(_("La fecha no puede estar en el futuro."))
        return started

    def save(self, commit=True):
        session = super().save(commit=False)
        session.ended_at = session.started_at + timedelta(minutes=self.cleaned_data["minutes"])
        session.is_logged = True
        if commit:
            session.save()
        return session


class GoalForm(NoColonMixin, forms.ModelForm):
    class Meta:
        model = Goal
        fields = ["name", "target_flux"]
        labels = {"name": _("¿Para qué estás ahorrando?"), "target_flux": _("Flux que necesitas")}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": _("Ej: Dragón nuevo, gemas, montura...")}),
            "target_flux": forms.NumberInput(attrs={"inputmode": "numeric", "min": 1}),
        }


class ProfileForm(NoColonMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["trove_name", "main_class"]
