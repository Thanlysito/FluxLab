from django import template
from django.utils.translation import get_language

register = template.Library()


@register.filter
def fnum(value):
    """1234567 -> '1.234.567' en español, '1,234,567' en ingles."""
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return value
    text = f"{n:,}"
    return text.replace(",", ".") if (get_language() or "es")[:2] == "es" else text


@register.filter
def hm(hours):
    """1.5 -> '1 h 30 min'; 0.25 -> '15 min'."""
    try:
        minutes = int(round(float(hours) * 60))
    except (TypeError, ValueError):
        return hours
    h, m = divmod(minutes, 60)
    return f"{h} h {m:02d} min" if h else f"{m} min"


@register.filter
def duration(td):
    """timedelta -> '1 h 05 min'."""
    return hm(td.total_seconds() / 3600) if td is not None else ""


@register.filter
def pct(value, total):
    """Porcentaje entero de value sobre total (para las barras)."""
    try:
        return max(0, min(100, round(float(value) * 100 / float(total))))
    except (TypeError, ValueError, ZeroDivisionError):
        return 0
