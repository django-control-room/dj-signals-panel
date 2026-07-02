"""
Tests for the dj_signals_panel_badge_variant template filter.
"""

from django.test import SimpleTestCase

from dj_signals_panel.templatetags.dj_signals_panel_tags import (
    _ALL_VARIANTS,
    dj_signals_panel_badge_variant,
)


class TestBadgeVariant(SimpleTestCase):
    def test_django_app_label_resolves_to_success_green(self):
        """Built-in Django signals report app_label="django" and must
        always render as the green/success badge, not a hashed colour."""
        self.assertEqual(
            dj_signals_panel_badge_variant("django"), "dcr-badge dcr-badge--success"
        )

    def test_same_app_label_always_maps_to_same_variant(self):
        result_a = dj_signals_panel_badge_variant("myapp")
        result_b = dj_signals_panel_badge_variant("myapp")
        self.assertEqual(result_a, result_b)

    def test_extra_variant_uses_panel_scoped_class(self):
        """Any app label hashing to one of the 8 extra hues should return
        a `dj-signals-panel-badge--<hue>` class alongside `dcr-badge`."""
        for app_label in (
            "alpha",
            "bravo",
            "charlie",
            "delta",
            "echo",
            "foxtrot",
            "golf",
            "hotel",
            "india",
        ):
            variant_class = dj_signals_panel_badge_variant(app_label)
            self.assertTrue(variant_class.startswith("dcr-badge"))

    def test_result_always_includes_base_dcr_badge_class(self):
        for app_label in ("auth", "django", "contenttypes", "app1", "sessions"):
            self.assertIn("dcr-badge", dj_signals_panel_badge_variant(app_label))
