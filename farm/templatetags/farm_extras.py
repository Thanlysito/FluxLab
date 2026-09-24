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
    """timedelta -> '1 h 05 min'. Por debajo de 10 minutos muestra los segundos
    ('4 min 47 s'), para que no parezca que una sesion de 4:47 duro 5 minutos."""
    if td is None:
        return ""
    secs = int(td.total_seconds())
    if secs < 600:
        m, s = divmod(secs, 60)
        return f"{m} min {s:02d} s" if m else f"{s} s"
    return hm(secs / 3600)


@register.filter
def pct(value, total):
    """Porcentaje entero de value sobre total (para las barras)."""
    try:
        return max(0, min(100, round(float(value) * 100 / float(total))))
    except (TypeError, ValueError, ZeroDivisionError):
        return 0
