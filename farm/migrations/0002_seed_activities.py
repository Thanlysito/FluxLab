"""Actividades de farmeo iniciales. Se pueden agregar mas desde el admin."""
from django.db import migrations

ACTIVITIES = [
    # (slug, nombre, nombre en ingles)
    ("delves", "Delves", "Delves"),
    ("geode-topside", "Geode (superficie)", "Geode Topside"),
    ("geode-caves", "Geode (cuevas)", "Geode Caves"),
    ("shadow-tower", "Shadow Tower", "Shadow Tower"),
    ("ships", "Barcos (Ships)", "Ships"),
    ("leviathans", "Leviatanes", "Leviathans"),
    ("dungeons", "Mazmorras (dungeons)", "Dungeons"),
    ("resources", "Recursos (minar, recolectar)", "Resources (mining, gathering)"),
    ("fishing", "Pesca", "Fishing"),
    ("other", "Otra", "Other"),
]


def seed(apps, schema_editor):
    Activity = apps.get_model("farm", "Activity")
    for order, (slug, name, name_en) in enumerate(ACTIVITIES):
        Activity.objects.update_or_create(slug=slug, defaults={"name": name, "name_en": name_en, "order": order})


def unseed(apps, schema_editor):
    apps.get_model("farm", "Activity").objects.filter(slug__in=[a[0] for a in ACTIVITIES]).delete()


class Migration(migrations.Migration):
    dependencies = [("farm", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
