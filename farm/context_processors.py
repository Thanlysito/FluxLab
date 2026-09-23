def running_session(request):
    """Deja disponible en todas las plantillas el cronometro que este corriendo."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    return {"running_session": user.farm_sessions.running().select_related("activity").first()}
