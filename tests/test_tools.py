"""
Tests for the MCP introspection tools exposed via conf.py's `tools=[...]`.

Handlers are called directly with a PanelToolContext (bypassing the MCP
transport/registry, which is exercised separately in dj-control-room). Fixture
data comes from example_project/app/{signals,handlers}.py:

- user_profile_created: two receivers, no sender filter
    - on_profile_created_log        (no dispatch_uid)
    - on_profile_created_welcome    (dispatch_uid="app.handlers.on_profile_created_welcome")
- order_confirmed: one receiver via @receiver(order_confirmed)
- notification_requested: three receivers, no sender filter
- report_generated: zero receivers
- django.db.models.signals.post_save:
    - on_user_saved      (sender=User)
    - on_any_user_saved  (no sender filter, via @receiver(post_save))
"""

from django.contrib.auth import get_user_model
from django.test import override_settings

from dj_control_room_base.core.panel_tool import PanelToolContext

from dj_signals_panel.conf import panel_config
from dj_signals_panel.tools import (
    handle_find_signal_by_sender,
    handle_get_receivers,
    handle_inspect_receiver,
    handle_list_signals,
)

from .base import SignalsPanelTestCase

User = get_user_model()

USER_PROFILE_CREATED = "app.signals.user_profile_created"
POST_SAVE = "django.db.models.signals.post_save"
PRE_SAVE = "django.db.models.signals.pre_save"


def _ctx(**inputs) -> PanelToolContext:
    return PanelToolContext(user=None, inputs=inputs, config=panel_config)


class TestListSignals(SignalsPanelTestCase):
    def test_returns_success(self):
        result = handle_list_signals(_ctx())
        self.assertTrue(result.success)

    def test_includes_app_and_builtin_signals(self):
        result = handle_list_signals(_ctx())
        signal_ids = {s["signal_id"] for s in result.data["signals"]}
        self.assertIn(USER_PROFILE_CREATED, signal_ids)
        self.assertIn(POST_SAVE, signal_ids)

    def test_app_label_filter(self):
        result = handle_list_signals(_ctx(app_label="app"))
        for s in result.data["signals"]:
            self.assertEqual(s["app_label"], "app")
        signal_ids = {s["signal_id"] for s in result.data["signals"]}
        self.assertIn(USER_PROFILE_CREATED, signal_ids)
        self.assertNotIn(POST_SAVE, signal_ids)

    def test_query_filter_matches_name_substring(self):
        result = handle_list_signals(_ctx(query="order_confirmed"))
        signal_ids = {s["signal_id"] for s in result.data["signals"]}
        self.assertEqual(signal_ids, {"app.signals.order_confirmed"})

    def test_query_filter_no_match_returns_empty(self):
        result = handle_list_signals(_ctx(query="no_such_signal_xyz"))
        self.assertEqual(result.data["signals"], [])

    def test_receiver_count_reflects_connected_receivers(self):
        result = handle_list_signals(_ctx())
        by_id = {s["signal_id"]: s for s in result.data["signals"]}
        self.assertEqual(by_id[USER_PROFILE_CREATED]["receiver_count"], 2)
        self.assertEqual(by_id["app.signals.report_generated"]["receiver_count"], 0)

    def test_senders_includes_bound_sender_for_post_save(self):
        result = handle_list_signals(_ctx())
        by_id = {s["signal_id"]: s for s in result.data["signals"]}
        self.assertIn("User", by_id[POST_SAVE]["senders"])

    def test_senders_empty_when_no_receiver_filters_sender(self):
        result = handle_list_signals(_ctx())
        by_id = {s["signal_id"]: s for s in result.data["signals"]}
        self.assertEqual(by_id[USER_PROFILE_CREATED]["senders"], [])


class TestGetReceivers(SignalsPanelTestCase):
    def test_missing_signal_input_fails(self):
        result = handle_get_receivers(_ctx())
        self.assertFalse(result.success)

    def test_unknown_signal_id_fails(self):
        result = handle_get_receivers(_ctx(signal="app.signals.no_such_signal"))
        self.assertFalse(result.success)

    def test_known_signal_lists_all_receivers(self):
        result = handle_get_receivers(_ctx(signal=USER_PROFILE_CREATED))
        self.assertTrue(result.success)
        names = {r["function_name"] for r in result.data["receivers"]}
        self.assertEqual(
            names, {"on_profile_created_log", "on_profile_created_welcome"}
        )

    def test_dotted_path_is_populated(self):
        result = handle_get_receivers(_ctx(signal=USER_PROFILE_CREATED))
        receiver = next(
            r
            for r in result.data["receivers"]
            if r["function_name"] == "on_profile_created_log"
        )
        self.assertEqual(receiver["dotted_path"], "app.handlers.on_profile_created_log")

    def test_dispatch_uid_none_when_not_provided(self):
        result = handle_get_receivers(_ctx(signal=USER_PROFILE_CREATED))
        receiver = next(
            r
            for r in result.data["receivers"]
            if r["function_name"] == "on_profile_created_log"
        )
        self.assertIsNone(receiver["dispatch_uid"])

    def test_dispatch_uid_resolved_when_provided(self):
        result = handle_get_receivers(_ctx(signal=USER_PROFILE_CREATED))
        receiver = next(
            r
            for r in result.data["receivers"]
            if r["function_name"] == "on_profile_created_welcome"
        )
        self.assertEqual(
            receiver["dispatch_uid"], "app.handlers.on_profile_created_welcome"
        )

    def test_ref_type_is_weak_or_strong_string(self):
        result = handle_get_receivers(_ctx(signal=USER_PROFILE_CREATED))
        for r in result.data["receivers"]:
            self.assertIn(r["ref_type"], ("weak", "strong"))

    def test_sender_filter_resolved_for_post_save(self):
        result = handle_get_receivers(_ctx(signal=POST_SAVE))
        receiver = next(
            r for r in result.data["receivers"] if r["function_name"] == "on_user_saved"
        )
        self.assertEqual(receiver["sender"], "User")
        self.assertEqual(receiver["sender_model"], "auth.User")

    def test_receiver_without_sender_filter_has_none_sender(self):
        result = handle_get_receivers(_ctx(signal=POST_SAVE))
        receiver = next(
            r
            for r in result.data["receivers"]
            if r["function_name"] == "on_any_user_saved"
        )
        self.assertIsNone(receiver["sender"])
        self.assertIsNone(receiver["sender_model"])

    def test_source_file_and_line_populated(self):
        result = handle_get_receivers(_ctx(signal=USER_PROFILE_CREATED))
        for r in result.data["receivers"]:
            self.assertTrue(r["source_file"].endswith("handlers.py"))
            self.assertIsInstance(r["source_line"], int)


class TestFindSignalBySender(SignalsPanelTestCase):
    def test_missing_model_input_fails(self):
        result = handle_find_signal_by_sender(_ctx())
        self.assertFalse(result.success)

    def test_unknown_model_fails(self):
        result = handle_find_signal_by_sender(_ctx(model="NoSuchModelXyz"))
        self.assertFalse(result.success)

    def test_bare_model_name_resolves(self):
        result = handle_find_signal_by_sender(_ctx(model="User"))
        self.assertTrue(result.success)
        self.assertEqual(result.data["model"], "auth.User")

    def test_dotted_model_name_resolves(self):
        result = handle_find_signal_by_sender(_ctx(model="auth.User"))
        self.assertTrue(result.success)
        self.assertEqual(result.data["model"], "auth.User")

    def test_post_save_appears_with_sender_match(self):
        result = handle_find_signal_by_sender(_ctx(model="User"))
        signals_by_id = {s["signal_id"]: s for s in result.data["signals"]}
        self.assertIn(POST_SAVE, signals_by_id)
        receivers = signals_by_id[POST_SAVE]["receivers"]
        on_user_saved = next(
            r for r in receivers if r["function_name"] == "on_user_saved"
        )
        self.assertEqual(on_user_saved["match_type"], "sender")

    def test_post_save_catch_all_receiver_also_included(self):
        """on_any_user_saved has no sender filter but post_save is a model
        lifecycle signal, so it genuinely fires whenever any model (including
        User) is saved."""
        result = handle_find_signal_by_sender(_ctx(model="User"))
        signals_by_id = {s["signal_id"]: s for s in result.data["signals"]}
        receivers = signals_by_id[POST_SAVE]["receivers"]
        on_any_user_saved = next(
            r for r in receivers if r["function_name"] == "on_any_user_saved"
        )
        self.assertEqual(on_any_user_saved["match_type"], "catch_all")

    def test_unrelated_custom_signal_not_included(self):
        """user_profile_created's receivers have no sender filter and it isn't
        a model lifecycle signal, so it must not be reported as firing for
        User saves."""
        result = handle_find_signal_by_sender(_ctx(model="User"))
        signal_ids = {s["signal_id"] for s in result.data["signals"]}
        self.assertNotIn(USER_PROFILE_CREATED, signal_ids)

    def test_lifecycle_signal_with_no_receivers_not_included(self):
        result = handle_find_signal_by_sender(_ctx(model="User"))
        signal_ids = {s["signal_id"] for s in result.data["signals"]}
        self.assertNotIn(PRE_SAVE, signal_ids)


class TestInspectReceiver(SignalsPanelTestCase):
    def test_missing_dotted_path_fails(self):
        result = handle_inspect_receiver(_ctx())
        self.assertFalse(result.success)

    def test_unresolvable_path_fails(self):
        result = handle_inspect_receiver(_ctx(dotted_path="no.such.module.func"))
        self.assertFalse(result.success)

    def test_no_dot_path_fails(self):
        result = handle_inspect_receiver(_ctx(dotted_path="lonely"))
        self.assertFalse(result.success)

    def test_non_callable_target_fails(self):
        """app.signals.user_profile_created is a Signal instance, not callable."""
        result = handle_inspect_receiver(_ctx(dotted_path=USER_PROFILE_CREATED))
        self.assertFalse(result.success)

    def test_resolves_plain_function(self):
        result = handle_inspect_receiver(
            _ctx(dotted_path="app.handlers.on_profile_created_log")
        )
        self.assertTrue(result.success)
        self.assertEqual(result.data["module"], "app.handlers")
        self.assertEqual(result.data["qualname"], "on_profile_created_log")

    def test_source_location_populated(self):
        result = handle_inspect_receiver(
            _ctx(dotted_path="app.handlers.on_profile_created_log")
        )
        self.assertTrue(result.data["source_file"].endswith("handlers.py"))
        self.assertIsInstance(result.data["source_line"], int)

    def test_docstring_captured(self):
        result = handle_inspect_receiver(
            _ctx(dotted_path="app.handlers.on_profile_created_log")
        )
        self.assertIn("Plain function receiver", result.data["docstring"])

    def test_connected_signals_lists_current_connections(self):
        result = handle_inspect_receiver(
            _ctx(dotted_path="app.handlers.on_profile_created_welcome")
        )
        connected = result.data["connected_signals"]
        self.assertEqual(len(connected), 1)
        self.assertEqual(connected[0]["signal_id"], USER_PROFILE_CREATED)
        self.assertEqual(
            connected[0]["dispatch_uid"], "app.handlers.on_profile_created_welcome"
        )

    @override_settings(DJ_SIGNALS_PANEL_SETTINGS={"SHOW_SOURCE": True})
    def test_show_source_true_populates_preview(self):
        result = handle_inspect_receiver(
            _ctx(dotted_path="app.handlers.on_profile_created_log")
        )
        self.assertIsNotNone(result.data["source_preview"])
        self.assertIn("def ", result.data["source_preview"])

    @override_settings(DJ_SIGNALS_PANEL_SETTINGS={"SHOW_SOURCE": False})
    def test_show_source_false_omits_preview_but_keeps_location(self):
        result = handle_inspect_receiver(
            _ctx(dotted_path="app.handlers.on_profile_created_log")
        )
        self.assertIsNone(result.data["source_preview"])
        self.assertIsNotNone(result.data["source_file"])
