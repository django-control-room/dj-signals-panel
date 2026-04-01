"""
Tests for the signals panel index (search) view.

The index view is the main landing page of the panel. It:
- Requires staff-level authentication
- Lists all discovered Django signals
- Filters by name/module/app via ?q=
- Filters by app label via ?app=
- Exposes stats and grouping data in context
"""

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from .base import CeleryPanelTestCase

User = get_user_model()

INDEX_URL = "/admin/dj-signals-panel/"


class TestIndexViewAccess(CeleryPanelTestCase):
    """Access control: who can and cannot reach the index view."""

    def test_staff_user_can_access_index(self):
        response = self.client.get(reverse("dj_signals_panel:index"))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_is_redirected_to_login(self):
        client = Client()
        response = client.get(reverse("dj_signals_panel:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_non_staff_user_is_redirected(self):
        regular_user = User.objects.create_user(
            username="regular", password="pass123", is_staff=False
        )
        client = Client()
        client.force_login(regular_user)
        response = client.get(reverse("dj_signals_panel:index"))
        self.assertEqual(response.status_code, 302)


class TestIndexViewRendering(CeleryPanelTestCase):
    """Template rendering and context structure for the index view."""

    def test_uses_correct_template(self):
        response = self.client.get(reverse("dj_signals_panel:index"))
        self.assertTemplateUsed(response, "admin/dj_signals_panel/index.html")

    def test_context_contains_expected_keys(self):
        response = self.client.get(reverse("dj_signals_panel:index"))
        expected_keys = (
            "signals",
            "stats",
            "grouped_signals",
            "search_query",
            "app_filter",
            "signal_apps",
            "total_displayed",
        )
        for key in expected_keys:
            self.assertIn(key, response.context, f"Missing context key: {key!r}")

    def test_signals_list_is_non_empty(self):
        """The panel always discovers at least the example app's signals."""
        response = self.client.get(reverse("dj_signals_panel:index"))
        self.assertGreater(len(response.context["signals"]), 0)

    def test_total_displayed_matches_signals_length(self):
        response = self.client.get(reverse("dj_signals_panel:index"))
        self.assertEqual(
            response.context["total_displayed"],
            len(response.context["signals"]),
        )

    def test_signal_apps_list_is_sorted(self):
        response = self.client.get(reverse("dj_signals_panel:index"))
        apps_list = response.context["signal_apps"]
        self.assertEqual(apps_list, sorted(apps_list))

    def test_grouped_signals_covers_all_signals(self):
        """Every signal in the flat list must appear in exactly one group."""
        response = self.client.get(reverse("dj_signals_panel:index"))
        signals = response.context["signals"]
        grouped = response.context["grouped_signals"]
        all_grouped_ids = {
            sig.signal_id
            for group_signals in grouped.values()
            for sig in group_signals
        }
        for sig in signals:
            self.assertIn(
                sig.signal_id,
                all_grouped_ids,
                f"Signal {sig.signal_id!r} is missing from grouped_signals",
            )

    def test_stats_total_signals_matches_list_length(self):
        response = self.client.get(reverse("dj_signals_panel:index"))
        signals = response.context["signals"]
        stats = response.context["stats"]
        self.assertEqual(stats.total_signals, len(signals))

    def test_stats_receivers_is_non_negative(self):
        response = self.client.get(reverse("dj_signals_panel:index"))
        stats = response.context["stats"]
        self.assertGreaterEqual(stats.total_receivers, 0)
        self.assertGreaterEqual(stats.signals_without_receivers, 0)


class TestIndexViewSearch(CeleryPanelTestCase):
    """Search query (?q=) behaviour on the index view."""

    def test_empty_q_param_returns_same_as_no_param(self):
        no_q = self.client.get(reverse("dj_signals_panel:index"))
        empty_q = self.client.get(reverse("dj_signals_panel:index") + "?q=")
        self.assertEqual(
            len(no_q.context["signals"]),
            len(empty_q.context["signals"]),
        )

    def test_search_query_is_echoed_in_context(self):
        response = self.client.get(
            reverse("dj_signals_panel:index") + "?q=user_profile"
        )
        self.assertEqual(response.context["search_query"], "user_profile")

    def test_whitespace_only_query_is_treated_as_empty(self):
        no_q = self.client.get(reverse("dj_signals_panel:index"))
        whitespace_q = self.client.get(
            reverse("dj_signals_panel:index") + "?q=   "
        )
        self.assertEqual(
            len(no_q.context["signals"]),
            len(whitespace_q.context["signals"]),
        )

    def test_search_returns_matching_signal(self):
        response = self.client.get(
            reverse("dj_signals_panel:index") + "?q=user_profile_created"
        )
        signals = response.context["signals"]
        self.assertGreaterEqual(len(signals), 1)
        names = [s.name for s in signals]
        self.assertIn("user_profile_created", names)

    def test_search_results_all_match_query(self):
        """Every returned signal must contain the query in name, module, id, or app."""
        query = "order_confirmed"
        response = self.client.get(
            reverse("dj_signals_panel:index") + f"?q={query}"
        )
        for sig in response.context["signals"]:
            haystack = (
                sig.name.lower()
                + sig.module.lower()
                + sig.signal_id.lower()
                + sig.app_label.lower()
            )
            self.assertIn(
                query,
                haystack,
                f"Signal {sig.name!r} does not match query {query!r}",
            )

    def test_search_is_case_insensitive(self):
        lower = self.client.get(
            reverse("dj_signals_panel:index") + "?q=order_confirmed"
        )
        upper = self.client.get(
            reverse("dj_signals_panel:index") + "?q=ORDER_CONFIRMED"
        )
        self.assertEqual(
            len(lower.context["signals"]),
            len(upper.context["signals"]),
        )

    def test_search_with_no_matches_returns_empty_list(self):
        response = self.client.get(
            reverse("dj_signals_panel:index") + "?q=zzznomatch_xyz_999"
        )
        self.assertEqual(response.context["signals"], [])
        self.assertEqual(response.context["total_displayed"], 0)


class TestIndexViewAppFilter(CeleryPanelTestCase):
    """App filter (?app=) behaviour on the index view."""

    def test_app_filter_is_echoed_in_context(self):
        response = self.client.get(reverse("dj_signals_panel:index") + "?app=app")
        self.assertEqual(response.context["app_filter"], "app")

    def test_app_filter_restricts_signals_to_named_app(self):
        response = self.client.get(reverse("dj_signals_panel:index") + "?app=app")
        signals = response.context["signals"]
        self.assertGreater(len(signals), 0)
        for sig in signals:
            self.assertEqual(
                sig.app_label,
                "app",
                f"Signal {sig.name!r} has app_label {sig.app_label!r}, expected 'app'",
            )

    def test_app_filter_with_unknown_app_returns_empty(self):
        response = self.client.get(
            reverse("dj_signals_panel:index") + "?app=no_such_app_xyz"
        )
        self.assertEqual(response.context["signals"], [])
        self.assertEqual(response.context["total_displayed"], 0)

    def test_combined_search_and_app_filter(self):
        """Search is applied first, then app filter narrows further."""
        response = self.client.get(
            reverse("dj_signals_panel:index") + "?q=order&app=app"
        )
        signals = response.context["signals"]
        for sig in signals:
            self.assertEqual(sig.app_label, "app")
            haystack = sig.name.lower() + sig.module.lower() + sig.signal_id.lower()
            self.assertIn("order", haystack)

    def test_app_filter_reduces_signal_count(self):
        """Filtering by a single app should return fewer signals than no filter."""
        all_signals = self.client.get(reverse("dj_signals_panel:index"))
        filtered = self.client.get(
            reverse("dj_signals_panel:index") + "?app=app"
        )
        self.assertLess(
            len(filtered.context["signals"]),
            len(all_signals.context["signals"]),
        )
