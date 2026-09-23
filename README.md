# FluxLab

Cronómetro y estadísticas de farmeo para **Trove**: dale a *Empezar* cuando entres a farmear, apunta el flux al terminar y FluxLab te dice qué actividad te rinde más por hora, cómo vas en la semana y cuántas horas te faltan para tu meta.

Proyecto de fans, sin afiliación con Gamigo ni Trion Worlds.

## Qué hace (MVP)

- Cronómetro de sesión (uno a la vez por usuario) y registro manual para sesiones sin cronometrar.
- Registro en ~20 s: actividad, flux, cubits, clase y Power Rank (recuerda la clase y el PR de la última vez).
- Inicio con los últimos 7 días: flux, horas, flux/h, racha y barras por día.
- Estadísticas por periodo (7 días, 30 días, todo) con flux/h por actividad y «lo que más te rinde».
- Metas de ahorro con progreso y horas estimadas según tu ritmo de los últimos 30 días.
- Español e inglés (`locale/en`).
- La casilla «contar en estadísticas de la comunidad» ya se guarda, para la futura página de promedios.

## Correr en tu PC

```powershell
py -3.13 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abre http://127.0.0.1:8000. Las actividades (Delves, Geode, Barcos, Leviatanes…) se crean solas con `migrate` y se editan en `/admin/`.

## Pruebas

```powershell
python manage.py test farm
```

## Traducciones

Los textos se escriben en español dentro de `{% translate %}` / `_()`. Para actualizar el inglés:

```powershell
python manage.py makemessages -l en
python tools/traduccion_en.py        # rellena lo que ya está en el diccionario y lista lo que falta
python manage.py compilemessages -l en
```

En Windows `makemessages`/`compilemessages` necesitan gettext (por ejemplo `winget install GnuWin32.GetText` o las herramientas de mlocati). El `.mo` compilado se sube al repo, así Railway no necesita gettext.

## Desplegar en Railway

1. Nuevo proyecto → *Deploy from GitHub repo* → este repositorio.
2. Agrega un servicio **PostgreSQL**; en el servicio web crea la variable `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`.
3. Variables del servicio web:
   - `DJANGO_DEBUG=False`
   - `DJANGO_SECRET_KEY=` (una clave larga aleatoria)
   - `DJANGO_ALLOWED_HOSTS=` tu dominio de Railway
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://` + ese dominio
4. El `Procfile` corre migraciones, `collectstatic` y gunicorn en cada deploy.

## Estructura

```
fluxlab/        configuración de Django
farm/           la app: modelos, vistas, estadísticas (stats.py), plantillas, CSS
locale/en/      traducción al inglés
tools/          traduccion_en.py
```
