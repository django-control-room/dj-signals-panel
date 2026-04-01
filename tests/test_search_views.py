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
from django.test import Client, override_settings
from django.urls import reverse

from .base import SignalsPanelTestCase

User = get_user_model()

INDEX_URL = "/admin/dj-signals-panel/"


class TestIndexViewAccess(SignalsPanelTestCase):
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


class TestIndexViewRendering(SignalsPanelTestCase):
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


class TestIndexViewSearch(SignalsPanelTestCase):
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


class TestIndexViewAppFilter(SignalsPanelTestCase):
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


class TestIndexViewSignalModules(SignalsPanelTestCase):
    """
    Tests for the SIGNAL_MODULES configuration option.

    SIGNAL_MODULES lets users point the panel at signal modules that are not
    named '{app}.signals' and therefore would not be discovered automatically.
    The fixture module 'app.events' is used for this purpose: it lives inside
    the example app but is never auto-scanned because it is not named 'signals'.
    """

    # Signals defined in the non-standard fixture module.
    EXTRA_MODULE = "app.events"
    EXTRA_SIGNAL_NAMES = {"user_invited", "export_completed"}

    def _signal_ids(self, response):
        return {s.signal_id for s in response.context["signals"]}

    def _signal_names(self, response):
        return {s.name for s in response.context["signals"]}

    def test_extra_module_not_discovered_without_setting(self):
        """app.events signals must be absent when SIGNAL_MODULES is empty."""
        with override_settings(DJ_SIGNALS_PANEL_SETTINGS={"SIGNAL_MODULES": []}):
            response = self.client.get(reverse("dj_signals_panel:index"))
        self.assertTrue(
            self._signal_names(response).isdisjoint(self.EXTRA_SIGNAL_NAMES),
            "app.events signals should not appear without SIGNAL_MODULES",
        )

    @override_settings(
        DJ_SIGNALS_PANEL_SETTINGS={"SIGNAL_MODULES": ["app.events"]}
    )
    def test_extra_module_signals_appear_when_configured(self):
        """Signals from app.events must appear when it is listed in SIGNAL_MODULES."""
        response = self.client.get(reverse("dj_signals_panel:index"))
        self.assertTrue(
            self.EXTRA_SIGNAL_NAMES.issubset(self._signal_names(response)),
            f"Expected {self.EXTRA_SIGNAL_NAMES} in discovered signals",
        )

    @override_settings(
        DJ_SIGNALS_PANEL_SETTINGS={"SIGNAL_MODULES": ["app.events"]}
    )
    def test_extra_module_signal_id_uses_module_path(self):
        """signal_id must be scoped to the extra module, not app.signals."""
        response = self.client.get(reverse("dj_signals_panel:index"))
        extra_ids = {
            sid for sid in self._signal_ids(response)
            if sid.startswith(self.EXTRA_MODULE)
        }
        self.assertEqual(
            extra_ids,
            {f"{self.EXTRA_MODULE}.{name}" for name in self.EXTRA_SIGNAL_NAMES},
        )

    @override_settings(
        DJ_SIGNALS_PANEL_SETTINGS={"SIGNAL_MODULES": ["app.events"]}
    )
    def test_extra_module_signals_have_correct_app_label(self):
        """Signals from app.events should resolve to the 'app' app label."""
        response = self.client.get(reverse("dj_signals_panel:index"))
        for sig in response.context["signals"]:
            if sig.name in self.EXTRA_SIGNAL_NAMES:
                self.assertEqual(
                    sig.app_label,
                    "app",
                    f"Expected app_label='app' for {sig.name!r}",
                )

    @override_settings(
        DJ_SIGNALS_PANEL_SETTINGS={"SIGNAL_MODULES": ["app.events"]}
    )
    def test_extra_module_signals_are_reachable_on_detail_view(self):
        """Signals surfaced via SIGNAL_MODULES must have a working detail page."""
        from django.urls import reverse as r
        signal_id = f"{self.EXTRA_MODULE}.user_invited"
        url = r("dj_signals_panel:signal_detail", kwargs={"signal_id": signal_id})
        with override_settings(DJ_SIGNALS_PANEL_SETTINGS={"SIGNAL_MODULES": ["app.events"]}):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["signal"].name, "user_invited")

    @override_settings(
        DJ_SIGNALS_PANEL_SETTINGS={"SIGNAL_MODULES": ["no.such.module.xyz"]}
    )
    def test_nonexistent_module_is_silently_skipped(self):
        """A bad module path in SIGNAL_MODULES must not crash the view."""
        response = self.client.get(reverse("dj_signals_panel:index"))
        self.assertEqual(response.status_code, 200)

    @override_settings(
        DJ_SIGNALS_PANEL_SETTINGS={"SIGNAL_MODULES": ["app.signals"]}
    )
    def test_already_scanned_module_does_not_produce_duplicates(self):
        """Listing an already-auto-scanned module must not duplicate its signals."""
        response = self.client.get(reverse("dj_signals_panel:index"))
        all_ids = [s.signal_id for s in response.context["signals"]]
        self.assertEqual(
            len(all_ids),
            len(set(all_ids)),
            "Duplicate signal_ids found — deduplication is broken",
        )

    @override_settings(
        DJ_SIGNALS_PANEL_SETTINGS={
            "SIGNAL_MODULES": ["app.events", "no.such.module.xyz"]
        }
    )
    def test_multiple_modules_mixed_valid_and_invalid(self):
        """Valid and invalid entries can coexist: valid signals appear, no crash."""
        response = self.client.get(reverse("dj_signals_panel:index"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            self.EXTRA_SIGNAL_NAMES.issubset(self._signal_names(response)),
        )
