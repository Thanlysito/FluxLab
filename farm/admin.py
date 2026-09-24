from django.contrib import admin

from .models import Activity, FarmSession, Goal, LootItem, Profile


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ("name", "name_en", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name_en",)}


class LootItemInline(admin.TabularInline):
    model = LootItem
    extra = 0


@admin.register(FarmSession)
class FarmSessionAdmin(admin.ModelAdmin):
    inlines = [LootItemInline]
    list_display = ("user", "activity", "started_at", "ended_at", "flux", "is_logged", "share_with_community")
    list_filter = ("activity", "is_logged", "share_with_community")
    search_fields = ("user__username",)
    date_hierarchy = "started_at"


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "target_flux", "created_at", "completed_at")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "trove_name", "main_class")
