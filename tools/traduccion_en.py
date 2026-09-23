"""Rellena locale/en/LC_MESSAGES/django.po con la traduccion al ingles.

Uso: python manage.py makemessages -l en && python tools/traduccion_en.py && python manage.py compilemessages
"""
from pathlib import Path

import polib

EN = {
    "Correo": "Email",
    "Solo para recuperar tu contraseña.": "Only used to recover your password.",
    "Actividad": "Activity",
    "Elige la actividad": "Pick the activity",
    "Flux ganado": "Flux earned",
    "Cubits ganados": "Cubits earned",
    "Clase": "Class",
    "Power Rank": "Power Rank",
    "Notas": "Notes",
    "Contar en las estadísticas de la comunidad (anónimo)": "Include in community stats (anonymous)",
    "¿Cuándo empezaste?": "When did you start?",
    "Duración (minutos)": "Duration (minutes)",
    "La fecha no puede estar en el futuro.": "The date can't be in the future.",
    "¿Para qué estás ahorrando?": "What are you saving for?",
    "Flux que necesitas": "Flux you need",
    "Ej: Dragón nuevo, gemas, montura...": "E.g. new dragon, gems, mount...",
    "nombre": "name",
    "nombre en inglés": "English name",
    "orden": "order",
    "activa": "active",
    "actividad": "activity",
    "actividades": "activities",
    "nombre en Trove": "Trove name",
    "clase principal": "main class",
    "clase": "class",
    "inicio": "start",
    "fin": "end",
    "flux ganado": "flux earned",
    "cubits ganados": "cubits earned",
    "notas": "notes",
    "contar en las estadísticas de la comunidad": "include in community stats",
    "meta": "goal",
    "flux objetivo": "target flux",
    "Cronometra tus sesiones de farmeo en Trove y descubre qué te da más flux por hora.":
        "Time your Trove farming sessions and find out what earns you the most flux per hour.",
    "Cronómetro en marcha": "Timer running",
    "Principal": "Main",
    "Inicio": "Home",
    "Historial": "History",
    "Estadísticas": "Stats",
    "Metas": "Goals",
    "Perfil": "Profile",
    "Salir": "Log out",
    "Entrar": "Log in",
    "Crear cuenta": "Sign up",
    "FluxLab es un proyecto de fans. No está afiliado con Gamigo ni Trion Worlds. Trove es marca de sus dueños.":
        "FluxLab is a fan project. It is not affiliated with Gamigo or Trion Worlds. Trove is a trademark of its owners.",
    "cumplida": "done",
    "faltan %(r)s": "%(r)s to go",
    "unas %(h)s a tu ritmo": "about %(h)s at your pace",
    "Marcar cumplida": "Mark as done",
    "Eliminar": "Delete",
    "No tienes metas todavía.": "You don't have any goals yet.",
    "Nueva meta": "New goal",
    "Solo cuenta el flux que anotes desde que la creas.": "Only flux you log after creating it counts.",
    "Crear meta": "Create goal",
    "Tu ritmo de los últimos 30 días: %(p)s flux/h.": "Your pace over the last 30 days: %(p)s flux/h.",
    "Anotar sesión": "Log session",
    "Fecha": "Date",
    "Duración": "Duration",
    "Flux": "Flux",
    "Flux/h": "Flux/h",
    "Editar": "Edit",
    "sin anotar": "not logged",
    "Anotar": "Log",
    "Anteriores": "Newer",
    "Página %(n)s de %(total)s": "Page %(n)s of %(total)s",
    "Siguientes": "Older",
    "Aún no hay sesiones. Dale a «Empezar» en el inicio la próxima vez que farmees.":
        "No sessions yet. Hit “Start” on the home page next time you farm.",
    "en marcha": "running",
    "Terminar y anotar": "Stop and log",
    "¿Vas a farmear?": "Going to farm?",
    "Actividad (la puedes cambiar al terminar)": "Activity (you can change it when you stop)",
    "Todavía no sé": "Not sure yet",
    "Empezar": "Start",
    "Anotar sin cronómetro": "Log without timer",
    "Te falta anotar": "Waiting to be logged",
    "Últimos 7 días": "Last 7 days",
    "Ver estadísticas": "See stats",
    "flux": "flux",
    "farmeando": "farming",
    "flux por hora": "flux per hour",
    "días de racha": "day streak",
    "Flux por día": "Flux per day",
    "Gestionar": "Manage",
    "¿Ahorrando para algo? Crea una meta y te decimos cuántas horas te faltan.":
        "Saving up for something? Create a goal and we'll tell you how many hours are left.",
    "Sesiones recientes": "Recent sessions",
    "Sin actividad": "No activity",
    "Aún no has anotado ninguna sesión.": "You haven't logged any sessions yet.",
    "Tu laboratorio de farmeo": "Your farming lab",
    "¿Cuánto flux te da <em>una hora</em> de farmeo?": "How much flux does <em>one hour</em> of farming get you?",
    "Dale a empezar cuando entres a farmear, apunta lo que ganaste al terminar y FluxLab te dice qué actividad rinde más, cuánto te falta para tu meta y cómo vas esta semana.":
        "Hit start when you go farming, jot down what you earned when you're done, and FluxLab tells you which activity pays best, how far you are from your goal and how your week is going.",
    "Crear cuenta gratis": "Sign up free",
    "Ya tengo cuenta": "I have an account",
    "Ejemplo": "Example",
    "Delves · en marcha": "Delves · running",
    "Flux por hora": "Flux per hour",
    "ejemplo": "example",
    "Barcos": "Ships",
    "Cronometra": "Time it",
    "Un botón al entrar, otro al salir. Si se te olvidó, la anotas a mano.":
        "One click when you start, one when you stop. Forgot? Log it by hand.",
    "Anota en 20 segundos": "Log it in 20 seconds",
    "Flux ganado, actividad y listo. Recordamos tu clase y tu Power Rank.":
        "Flux earned, activity, done. We remember your class and Power Rank.",
    "Farmea mejor": "Farm smarter",
    "Ve qué te rinde más y cuántas horas te faltan para esa montura o ese mag.":
        "See what pays best and how many hours until that mount or mag rider.",
    "Cuenta: %(u)s": "Account: %(u)s",
    "Guardar": "Save",
    "Cambiar contraseña": "Change password",
    "Corregir sesión": "Edit session",
    "¿Cuánto sacaste?": "How much did you get?",
    "Descartar esta sesión": "Discard this session",
    "Anotar una sesión": "Log a session",
    "Para cuando farmeaste sin el cronómetro.": "For when you farmed without the timer.",
    "Periodo": "Period",
    "7 días": "7 days",
    "30 días": "30 days",
    "Todo": "All time",
    "cubits": "cubits",
    "Lo que más te rinde": "Your best earner",
    "%(fph)s flux por hora de media.": "%(fph)s flux per hour on average.",
    "Flux por hora según actividad": "Flux per hour by activity",
    "Las actividades con menos de 30 minutos anotados no cuentan para «lo que más te rinde».":
        "Activities with less than 30 minutes logged don't count for “your best earner”.",
    "No hay sesiones anotadas en este periodo.": "No sessions logged in this period.",
    "Empezar a farmear": "Start farming",
    "¿Olvidaste tu contraseña?": "Forgot your password?",
    "Contraseña cambiada": "Password changed",
    "Tu contraseña se actualizó.": "Your password was updated.",
    "Volver al inicio": "Back to home",
    "Listo. Ya puedes entrar con tu nueva contraseña.": "Done. You can now log in with your new password.",
    "Nueva contraseña": "New password",
    "Guardar contraseña": "Save password",
    "El enlace ya no sirve (quizá ya se usó). Pide uno nuevo.":
        "This link no longer works (maybe it was already used). Ask for a new one.",
    "Pedir otro enlace": "Get a new link",
    "Revisa tu correo": "Check your email",
    "Si hay una cuenta con ese correo, te llegará un enlace en unos minutos. Mira también en spam.":
        "If there's an account with that email, a link will arrive in a few minutes. Check your spam folder too.",
    "Hola": "Hi",
    "Alguien (ojalá tú) pidió cambiar la contraseña de tu cuenta de FluxLab. Abre este enlace para poner una nueva:":
        "Someone (hopefully you) asked to reset the password of your FluxLab account. Open this link to set a new one:",
    "Si no fuiste tú, ignora este correo.": "If it wasn't you, just ignore this email.",
    "Recuperar contraseña": "Reset password",
    "Escribe tu correo y te mandamos un enlace para poner una nueva.":
        "Enter your email and we'll send you a link to set a new one.",
    "Enviar enlace": "Send link",
    "Recupera tu contraseña de FluxLab": "Reset your FluxLab password",
    "¿Ya tienes cuenta?": "Already have an account?",
    "¡Bienvenido a FluxLab! Dale a «Empezar» la próxima vez que farmees.":
        "Welcome to FluxLab! Hit “Start” next time you farm.",
    "Ya tienes un cronómetro corriendo.": "You already have a timer running.",
    "Sesión guardada: %(flux)s flux en %(time)s (%(fph)s flux/h).":
        "Session saved: %(flux)s flux in %(time)s (%(fph)s flux/h).",
    "Sesión guardada.": "Session saved.",
    "Sesión eliminada.": "Session deleted.",
    "Meta creada. El flux que registres desde ahora cuenta para ella.":
        "Goal created. Flux you log from now on counts toward it.",
    "¡Meta cumplida! 🎉": "Goal reached! 🎉",
    "Meta eliminada.": "Goal deleted.",
    "Perfil actualizado.": "Profile updated.",
    "Sesión guardada: %(flux)s flux. Duró menos de %(min)s minutos, así que no cuenta para el flux por hora.":
        "Session saved: %(flux)s flux. It lasted less than %(min)s minutes, so it doesn't count toward flux per hour.",
    "Duró menos de %(m)s minutos: se guarda el flux, pero no cuenta para el flux por hora.":
        "It lasted less than %(m)s minutes: the flux is saved, but it doesn't count toward flux per hour.",
    "Menos de 5 minutos: no cuenta para el flux/h": "Less than 5 minutes: doesn't count toward flux/h",
}
PLURALS = {
    "en %(n)s sesión": ["in %(n)s session", "in %(n)s sessions"],
}

if __name__ == "__main__":
    path = Path(__file__).resolve().parent.parent / "locale/en/LC_MESSAGES/django.po"
    po = polib.pofile(str(path))
    po.metadata_is_fuzzy = False
    po.metadata["Plural-Forms"] = "nplurals=2; plural=(n != 1);"
    missing = []
    for e in po:
        if e.msgid_plural:
            if e.msgid in PLURALS:
                e.msgstr_plural = dict(enumerate(PLURALS[e.msgid]))
            else:
                missing.append(e.msgid)
        elif e.msgid in EN:
            e.msgstr = EN[e.msgid]
        else:
            missing.append(e.msgid)
        if "fuzzy" in e.flags:
            e.flags.remove("fuzzy")
    po.save()
    print(f"{len(po) - len(missing)}/{len(po)} traducidas")
    for m in missing:
        print("  FALTA:", m)
