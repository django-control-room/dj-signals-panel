"""
Tests for the signals panel detail view.

The detail view shows full information about a single signal, identified by its
dotted signal_id path (e.g. "app.signals.user_profile_created"). It:
- Requires staff-level authentication
- Returns HTTP 404 for unknown or malformed signal IDs
- Provides the signal's metadata and its connected receivers in context
- Renders source file/line locations and optional source previews per receiver
"""

from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.urls import reverse

from .base import SignalsPanelTestCase

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


class TestDetailViewAccess(SignalsPanelTestCase):
    """Access control: who can and cannot reach the detail view."""

    def test_staff_user_can_access_detail(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user_is_redirected_to_login(self):
        client = Client()
        response = client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_non_staff_user_gets_permission_denied(self):
        regular_user = User.objects.create_user(
            username="regular", password="pass123", is_staff=False
        )
        client = Client()
        client.force_login(regular_user)
        response = client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertEqual(response.status_code, 403)

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


class TestDetailViewRendering(SignalsPanelTestCase):
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


class TestDetailViewSignalData(SignalsPanelTestCase):
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


class TestDetailViewReceiverData(SignalsPanelTestCase):
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


class TestDetailViewSenderResolution(SignalsPanelTestCase):
    """
    Sender resolution: a receiver connected with sender=SomeModel must show
    a readable label instead of the raw `<sender id=...>` memory pointer.
    """

    def test_sender_filtered_receiver_resolves_to_model_label(self):
        """on_user_saved is connected via post_save.connect(..., sender=User)."""
        response = self.client.get(detail_url(BUILTIN_SIGNAL_ID))
        receivers = response.context["receivers"]
        on_user_saved = next(
            r for r in receivers if r.function_name == "on_user_saved"
        )
        self.assertEqual(on_user_saved.sender, "User")

    def test_sender_label_is_never_a_raw_pointer(self):
        response = self.client.get(detail_url(BUILTIN_SIGNAL_ID))
        for r in response.context["receivers"]:
            if r.sender is not None:
                self.assertNotIn("id=", r.sender)
                self.assertNotIn("<sender", r.sender)

    def test_receiver_without_sender_filter_has_none_sender(self):
        """on_any_user_saved is connected with no sender filter (matches any)."""
        response = self.client.get(detail_url(BUILTIN_SIGNAL_ID))
        receivers = response.context["receivers"]
        on_any_user_saved = next(
            r for r in receivers if r.function_name == "on_any_user_saved"
        )
        self.assertIsNone(on_any_user_saved.sender)


class TestDetailViewSourceLocation(SignalsPanelTestCase):
    """
    Tests for source file and line number resolution on ReceiverInfo.

    source_file / source_line are resolved via inspect and are always
    populated when the handler is a plain Python function (regardless of
    the SHOW_SOURCE setting).
    """

    def test_receivers_have_source_file_populated(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        for r in response.context["receivers"]:
            self.assertIsNotNone(
                r.source_file,
                f"Expected source_file for receiver {r.function_name!r}",
            )

    def test_source_file_is_absolute_path_string(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        for r in response.context["receivers"]:
            self.assertIsInstance(r.source_file, str)
            self.assertTrue(
                r.source_file.startswith("/"),
                f"Expected an absolute path, got {r.source_file!r}",
            )

    def test_source_file_points_to_handlers_module(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        for r in response.context["receivers"]:
            self.assertTrue(
                r.source_file.endswith("handlers.py"),
                f"Expected source_file to end with 'handlers.py', got {r.source_file!r}",
            )

    def test_receivers_have_source_line_populated(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        for r in response.context["receivers"]:
            self.assertIsNotNone(
                r.source_line,
                f"Expected source_line for receiver {r.function_name!r}",
            )

    def test_source_line_is_positive_integer(self):
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        for r in response.context["receivers"]:
            self.assertIsInstance(r.source_line, int)
            self.assertGreater(r.source_line, 0)

    def test_template_renders_source_location(self):
        """The detail page renders 'handlers.py' as the source location."""
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertContains(response, "handlers.py")


class TestDetailViewSourcePreview(SignalsPanelTestCase):
    """
    Tests for the optional source preview feature (SHOW_SOURCE setting).

    The collapsible <details> block itself is keyed off source_file, not
    SHOW_SOURCE - it's how the (potentially long) file:line location is
    displayed regardless of the setting. When SHOW_SOURCE=True, each
    receiver's source code is additionally fetched into
    ReceiverInfo.source_preview and rendered inside that same block, along
    with the highlight.js assets and a "View Source" label. When
    SHOW_SOURCE=False, source_preview is None, no code or highlight.js is
    included, and the block is labelled "View Location" instead.
    """

    def test_show_source_true_populates_source_preview(self):
        """With SHOW_SOURCE=True the source_preview field is a non-empty string."""
        with override_settings(DJ_SIGNALS_PANEL_SETTINGS={"SHOW_SOURCE": True}):
            response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        for r in response.context["receivers"]:
            self.assertIsNotNone(
                r.source_preview,
                f"Expected source_preview for {r.function_name!r} when SHOW_SOURCE=True",
            )
            self.assertGreater(len(r.source_preview), 0)

    def test_show_source_true_preview_contains_function_def(self):
        """The source preview should contain the 'def' line of the handler."""
        with override_settings(DJ_SIGNALS_PANEL_SETTINGS={"SHOW_SOURCE": True}):
            response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        for r in response.context["receivers"]:
            self.assertIn(
                "def ",
                r.source_preview,
                f"source_preview for {r.function_name!r} does not contain a 'def' line",
            )

    @override_settings(DJ_SIGNALS_PANEL_SETTINGS={"SHOW_SOURCE": False})
    def test_show_source_false_leaves_source_preview_none(self):
        """With SHOW_SOURCE=False source_preview must be None on every receiver."""
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        for r in response.context["receivers"]:
            self.assertIsNone(
                r.source_preview,
                f"Expected source_preview=None for {r.function_name!r} when SHOW_SOURCE=False",
            )

    def test_show_source_true_renders_source_preview_block(self):
        """With SHOW_SOURCE=True the page includes the collapsible source block."""
        with override_settings(DJ_SIGNALS_PANEL_SETTINGS={"SHOW_SOURCE": True}):
            response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertContains(response, "source-preview-details")
        self.assertContains(response, "View Source")

    @override_settings(DJ_SIGNALS_PANEL_SETTINGS={"SHOW_SOURCE": False})
    def test_show_source_false_omits_code_but_keeps_location(self):
        """With SHOW_SOURCE=False the block still renders (for the file:line
        location) but must not include source code or the "View Source" label."""
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertContains(response, "source-preview-details")
        self.assertContains(response, "View Location")
        self.assertNotContains(response, "View Source")
        self.assertNotContains(response, "language-python")

    def test_show_source_true_includes_highlight_js(self):
        """With SHOW_SOURCE=True the page loads the highlight.js asset."""
        with override_settings(DJ_SIGNALS_PANEL_SETTINGS={"SHOW_SOURCE": True}):
            response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertContains(response, "highlight.min.js")

    @override_settings(DJ_SIGNALS_PANEL_SETTINGS={"SHOW_SOURCE": False})
    def test_show_source_false_excludes_highlight_js(self):
        """With SHOW_SOURCE=False the highlight.js asset must not be loaded."""
        response = self.client.get(detail_url(KNOWN_SIGNAL_ID))
        self.assertNotContains(response, "highlight.min.js")
