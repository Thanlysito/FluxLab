from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Activity, FarmSession, Goal
from .stats import user_stats
from .templatetags.farm_extras import fnum, hm, pct


def make_session(user, minutes=60, flux=10000, activity=None, days_ago=0, **kw):
    start = timezone.now() - timedelta(days=days_ago, minutes=minutes)
    return FarmSession.objects.create(
        user=user, activity=activity, started_at=start,
        ended_at=start + timedelta(minutes=minutes), flux=flux, is_logged=True, **kw,
    )


class Base(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("juan", "j@example.com", "clave-segura-123")
        self.delves = Activity.objects.get(slug="delves")
        self.ships = Activity.objects.get(slug="ships")
        self.client.force_login(self.user)


class PagesTest(Base):
    def test_landing_for_anonymous(self):
        self.client.logout()
        r = self.client.get("/")
        self.assertContains(r, "Crear cuenta gratis")

    def test_all_pages_render_empty_and_with_data(self):
        names = ["farm:home", "farm:history", "farm:stats", "farm:goals", "farm:profile", "farm:session_new"]
        for name in names:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        make_session(self.user, activity=self.delves)
        make_session(self.user, activity=self.ships, days_ago=1, flux=3000)
        Goal.objects.create(user=self.user, name="Montura", target_flux=500000)
        FarmSession.objects.create(user=self.user, activity=self.delves)  # corriendo
        for name in names:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        for period in ("7", "30", "all", "basura"):
            self.assertEqual(self.client.get(reverse("farm:stats"), {"period": period}).status_code, 200)

    def test_auth_pages(self):
        self.client.logout()
        for name in ("login", "signup", "password_reset"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_english(self):
        self.client.post(reverse("set_language"), {"language": "en", "next": "/"})
        r = self.client.get("/")
        self.assertContains(r, 'lang="en"')
        self.assertContains(r, "Going to farm?")
        self.assertContains(self.client.get(reverse("farm:stats")), "All time")

    def test_private_pages_need_login(self):
        self.client.logout()
        r = self.client.get(reverse("farm:history"))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse("login"), r["Location"])


class TimerFlowTest(Base):
    def test_start_stop_log(self):
        self.client.post(reverse("farm:session_start"), {"activity": self.delves.pk})
        session = FarmSession.objects.get(user=self.user)
        self.assertTrue(session.is_running)
        self.assertContains(self.client.get("/"), "Terminar y anotar")

        # un segundo "empezar" no crea otra
        self.client.post(reverse("farm:session_start"))
        self.assertEqual(FarmSession.objects.filter(user=self.user).count(), 1)

        r = self.client.post(reverse("farm:session_stop"))
        self.assertRedirects(r, reverse("farm:session_log", args=[session.pk]))
        r = self.client.post(reverse("farm:session_log", args=[session.pk]), {
            "activity": self.delves.pk, "flux": 12000, "cubits": 300,
            "trove_class": "", "power_rank": "", "notes": "", "share_with_community": "on",
        })
        self.assertRedirects(r, reverse("farm:home"))
        session.refresh_from_db()
        self.assertTrue(session.is_logged)
        self.assertEqual(session.flux, 12000)

    def test_cannot_touch_other_users_sessions(self):
        other = User.objects.create_user("otro", "o@example.com", "clave-segura-123")
        s = make_session(other)
        self.assertEqual(self.client.get(reverse("farm:session_log", args=[s.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("farm:session_delete", args=[s.pk])).status_code, 404)

    def test_manual_session(self):
        start = (timezone.localtime() - timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M")
        r = self.client.post(reverse("farm:session_new"), {
            "started_at": start, "minutes": 90, "activity": self.ships.pk, "flux": 9000,
            "cubits": 0, "trove_class": "", "power_rank": "", "notes": "",
        })
        self.assertRedirects(r, reverse("farm:home"))
        s = FarmSession.objects.get(user=self.user)
        self.assertEqual(s.duration, timedelta(minutes=90))
        self.assertEqual(s.flux_per_hour, 6000)

    def test_manual_session_rejects_future(self):
        start = (timezone.localtime() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M")
        r = self.client.post(reverse("farm:session_new"), {
            "started_at": start, "minutes": 60, "activity": self.ships.pk, "flux": 1,
        })
        self.assertEqual(r.status_code, 200)
        self.assertFalse(FarmSession.objects.exists())


class StatsTest(Base):
    def test_numbers(self):
        make_session(self.user, minutes=60, flux=20000, activity=self.delves)
        make_session(self.user, minutes=120, flux=20000, activity=self.ships, days_ago=1)
        make_session(self.user, minutes=10, flux=90000, activity=self.ships, days_ago=40)
        st = user_stats(self.user, since=timezone.now() - timedelta(days=7))
        self.assertEqual(st.sessions, 2)
        self.assertEqual(st.flux, 40000)
        self.assertEqual(st.by_activity[0].activity, self.delves)
        self.assertEqual(st.best_activity.activity, self.delves)
        self.assertEqual(st.streak, 2)
        self.assertEqual(len(st.last_7_days), 7)

    def test_seconds_long_session_does_not_explode_flux_per_hour(self):
        # Caso real: 1.000.000 de flux anotado en una sesion de 27 segundos.
        start = timezone.now() - timedelta(seconds=27)
        s = FarmSession.objects.create(user=self.user, activity=self.delves, started_at=start,
                                       ended_at=timezone.now(), flux=1_000_000, is_logged=True)
        make_session(self.user, minutes=60, flux=20000, activity=self.delves)
        st = user_stats(self.user)
        self.assertEqual(st.flux, 1_020_000)          # el flux si se suma
        self.assertEqual(st.flux_per_hour, 20000)     # pero no el ritmo
        self.assertEqual(st.by_activity[0].flux_per_hour, 20000)
        self.assertIsNone(s.flux_per_hour)
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get(reverse("farm:history")).status_code, 200)

    def test_short_lucky_session_is_not_best(self):
        make_session(self.user, minutes=10, flux=50000, activity=self.ships)
        make_session(self.user, minutes=60, flux=20000, activity=self.delves)
        self.assertEqual(user_stats(self.user).best_activity.activity, self.delves)

    def test_goal_counts_only_after_creation(self):
        make_session(self.user, flux=5000, days_ago=2)
        goal = Goal.objects.create(user=self.user, name="Mag", target_flux=10000)
        make_session(self.user, minutes=5, flux=4000)
        FarmSession.objects.filter(flux=4000).update(started_at=timezone.now())
        self.assertEqual(goal.earned, 4000)
        self.assertEqual(goal.percent, 40)


class FiltersTest(TestCase):
    def test_filters(self):
        self.assertEqual(fnum(1234567), "1.234.567")
        self.assertEqual(hm(1.5), "1 h 30 min")
        self.assertEqual(hm(0.25), "15 min")
        self.assertEqual(pct(5, 10), 50)
        self.assertEqual(pct(5, 0), 0)


class SignupTest(TestCase):
    def test_signup_logs_in_and_creates_profile(self):
        r = self.client.post(reverse("signup"), {
            "username": "nuevo", "email": "n@example.com",
            "password1": "una-clave-larga-99", "password2": "una-clave-larga-99",
        })
        self.assertRedirects(r, reverse("farm:home"))
        user = User.objects.get(username="nuevo")
        self.assertTrue(hasattr(user, "profile"))


class ModApiTest(Base):
    url = "/api/sesiones/"

    def setUp(self):
        super().setUp()
        self.key = self.user.profile.new_api_key() if hasattr(self.user, "profile") else None
        if self.key is None:
            from .models import Profile
            self.key = Profile.objects.create(user=self.user).new_api_key()
        self.client.logout()
        now = int(timezone.now().timestamp())
        self.payload = {"started_at": now - 111, "ended_at": now, "flux_start": 493846544, "flux_end": 493846794}

    def post(self, payload, key=None):
        import json
        return self.client.post(self.url, json.dumps(payload), content_type="application/json",
                                HTTP_AUTHORIZATION=f"Token {key or self.key}")

    def test_creates_session_from_mod(self):
        r = self.post(self.payload)
        self.assertEqual(r.status_code, 201, r.content)
        s = FarmSession.objects.get(user=self.user)
        self.assertEqual((s.flux, s.source, s.is_logged), (250, "mod", True))
        self.assertEqual(r.json()["flux"], 250)

    def test_same_session_twice_is_saved_once(self):
        self.post(self.payload)
        r = self.post(self.payload)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(FarmSession.objects.filter(user=self.user).count(), 1)

    def test_rejects_bad_key_and_bad_data(self):
        self.assertEqual(self.post(self.payload, key="fl_nope").status_code, 401)
        self.assertEqual(self.client.post(self.url, "{}", content_type="application/json").status_code, 401)
        self.assertEqual(self.post({**self.payload, "ended_at": self.payload["started_at"]}).status_code, 400)
        self.assertEqual(self.post({"started_at": 1}).status_code, 400)
        self.assertFalse(FarmSession.objects.exists())

    def test_spent_flux_counts_as_zero_and_activity_optional(self):
        r = self.post({**self.payload, "flux_end": 100, "activity": "delves"})
        s = FarmSession.objects.get(user=self.user)
        self.assertEqual((s.flux, s.activity.slug), (0, "delves"))

    def test_regenerating_key_invalidates_old_one(self):
        self.client.force_login(self.user)
        self.client.post(reverse("farm:api_key"))
        r = self.client.get(reverse("farm:profile"))
        self.assertContains(r, "fl_")
        self.assertNotContains(self.client.get(reverse("farm:profile")), 'value="fl_')
        self.client.logout()
        self.assertEqual(self.post(self.payload).status_code, 401)
