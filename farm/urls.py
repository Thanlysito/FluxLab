from django.urls import path

from . import views

app_name = "farm"

urlpatterns = [
    path("", views.home, name="home"),
    path("sesion/empezar/", views.session_start, name="session_start"),
    path("sesion/terminar/", views.session_stop, name="session_stop"),
    path("sesion/nueva/", views.session_new, name="session_new"),
    path("sesion/<int:pk>/", views.session_log, name="session_log"),
    path("sesion/<int:pk>/eliminar/", views.session_delete, name="session_delete"),
    path("historial/", views.history, name="history"),
    path("estadisticas/", views.stats, name="stats"),
    path("metas/", views.goals, name="goals"),
    path("metas/<int:pk>/cumplida/", views.goal_complete, name="goal_complete"),
    path("metas/<int:pk>/eliminar/", views.goal_delete, name="goal_delete"),
    path("perfil/", views.profile, name="profile"),
    path("perfil/clave/", views.api_key, name="api_key"),
]
