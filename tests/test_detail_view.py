"""
Tests for the signals panel detail view.

The detail view shows full information about a single signal, identified by its
dotted signal_id path (e.g. "app.signals.user_profile_created"). It:
- Requires staff-level authentication
- Returns HTTP 404 for unknown or malformed signal IDs
- Provides the signal's metadata and its connected receivers in context
"""

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from .base import CeleryPanelTestCase

User = get_user_model()

# A signal we know is always present and has receivers connected via AppConfig.ready().
KNOWN_SIGNAL_ID = "app.signals.user_profile_created"

# A signal with no receivers connected in the example project.
NO_RECEIVERS_SIGNAL_ID = "app.signals.report_generated"

# A Django built-in signal reachable by the panel.
BUILTIN_SIGNAL_ID = "django.db.models.signals.post_save"


def detail_url(signal_id: str) -> str:
    return reverse(
        "dj_signals_panel:signal_detail", kwargs={"signal_id": signal_id}
    )


class TestDetailViewAccess(CeleryPanelTestCase):
    """Access control: who can and cannot reach the detail view."""

    def test_staff_user_can_access_detail(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_is_redirected_to_login(self):
        client = Client()
        response = client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_non_staff_user_is_redirected(self):
        regular_user = User.objects.create_user(
            username="regular", password="pass123", is_staff=False
        )
        client = Client()
        client.force_login(regular_user)
        response = client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertEqual(response.status_code, 302)

    def test_unknown_signal_id_returns_404(self):
        response = self.client.get(detail_url("app.signals.no_such_signal_xyz"))
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_module_returns_404(self):
        response = self.client.get(detail_url("no_such_module.signals.some_signal"))
        self.assertEqual(response.status_code, 404)

    def test_malformed_signal_id_with_no_dot_returns_404(self):
        """A signal_id with no dot cannot be split into module + name."""
        response = self.client.get(detail_url("nodot"))
        self.assertEqual(response.status_code, 404)

    def test_attribute_that_is_not_a_signal_returns_404(self):
        """Pointing at a real module attribute that isn't a Signal returns 404."""
        response = self.client.get(detail_url("django.db.models.signals.Signal"))
        self.assertEqual(response.status_code, 404)


class TestDetailViewRendering(CeleryPanelTestCase):
    """Template and context structure for the detail view."""

    def test_uses_correct_template(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertTemplateUsed(response, "admin/dj_signals_panel/detail.html")

    def test_context_contains_signal(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertIn("signal", response.context)

    def test_context_contains_receivers(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertIn("receivers", response.context)

    def test_context_receivers_matches_signal_receivers(self):
        """The top-level receivers key is the same list as signal.receivers."""
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertEqual(
            response.context["receivers"],
            response.context["signal"].receivers,
        )

    def test_page_contains_signal_name(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertContains(response, "user_profile_created")


class TestDetailViewSignalData(CeleryPanelTestCase):
    """Data accuracy: the signal metadata returned by the detail view."""

    def test_signal_name_matches_requested_id(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        signal = response.context["signal"]
        self.assertEqual(signal.name, "user_profile_created")

    def test_signal_module_is_correct(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        signal = response.context["signal"]
        self.assertEqual(signal.module, "app.signals")

    def test_signal_id_is_preserved_in_detail(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        signal = response.context["signal"]
        self.assertEqual(signal.signal_id, KNOWN_SIGNAL_ID)

    def test_signal_app_label_is_correct(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        signal = response.context["signal"]
        self.assertEqual(signal.app_label, "app")

    def test_builtin_signal_is_accessible(self):
        """Django built-in signals (e.g. post_save) must be reachable by signal_id."""
        response = self.client.get(detail_url(BUILTIN_SIGNAL_ID))
        self.assertEqual(response.status_code, 200)
        signal = response.context["signal"]
        self.assertEqual(signal.name, "post_save")
        self.assertEqual(signal.module, "django.db.models.signals")


class TestDetailViewReceiverData(CeleryPanelTestCase):
    """Data accuracy: receiver information on the detail view."""

    def test_signal_with_receivers_lists_them(self):
        """user_profile_created has two receivers wired in AppConfig.ready()."""
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        receivers = response.context["receivers"]
        self.assertGreater(
            len(receivers),
            0,
            "Expected user_profile_created to have at least one receiver",
        )

    def test_signal_without_receivers_shows_empty_list(self):
        """report_generated has no handlers connected in the example project."""
        response = self.client.get(detail_url(NO_RECEIVERS_SIGNAL_ID))
        self.assertEqual(response.status_code, 200)
        receivers = response.context["receivers"]
        self.assertEqual(receivers, [])

    def test_receiver_info_has_required_fields(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        receivers = response.context["receivers"]
        self.assertGreater(len(receivers), 0)
        first = receivers[0]
        for field in ("function_name", "qualname", "module", "source_file", "source_line"):
            self.assertTrue(
                hasattr(first, field),
                f"ReceiverInfo is missing field {field!r}",
            )

    def test_receiver_function_names_are_strings(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        for receiver in response.context["receivers"]:
            self.assertIsInstance(receiver.function_name, str)
            self.assertTrue(
                len(receiver.function_name) > 0,
                "function_name should not be empty",
            )

    def test_known_receiver_function_appears_in_list(self):
        """on_profile_created_log is connected unconditionally in connect_all()."""
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        receiver_names = [r.function_name for r in response.context["receivers"]]
        self.assertIn("on_profile_created_log", receiver_names)

    def test_dispatch_uid_receiver_appears_once(self):
        """on_profile_created_welcome is connected with a dispatch_uid so it
        should appear exactly once regardless of how many times connect_all()
        is called."""
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        receiver_names = [r.function_name for r in response.context["receivers"]]
        count = receiver_names.count("on_profile_created_welcome")
        self.assertEqual(count, 1)
