"""
Tests for Django Admin integration with Dj Signals Panel.

The Dj Signals Panel integrates with Django Admin through a placeholder model
that appears in the admin interface and redirects to the Panel when clicked.
"""

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from .base import SignalsPanelTestCase


User = get_user_model()


class TestAdminIntegration(SignalsPanelTestCase):
    """Test cases for Django Admin integration."""

    def test_signals_panel_appears_in_admin_index(self):
        """Test that the Panel appears in the Django admin index page."""
        response = self.client.get("/admin/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "dj_signals_panel")

        changelist_url = reverse(
            "admin:dj_signals_panel_signalspanelplaceholder_changelist"
        )
        self.assertContains(response, changelist_url)

    def test_signals_panel_changelist_redirects_to_index(self):
        """Test that clicking the Panel in admin redirects to the Panel index."""
        changelist_url = reverse(
            "admin:dj_signals_panel_signalspanelplaceholder_changelist"
        )
        response = self.client.get(changelist_url)

        self.assertEqual(response.status_code, 302)
        expected_url = reverse("dj_signals_panel:index")
        self.assertRedirects(response, expected_url)

    def test_unauthenticated_user_cannot_access_admin_signals_panel(self):
        """Test that unauthenticated users cannot access the Panel through admin."""
        client = Client()
        changelist_url = reverse(
            "admin:dj_signals_panel_signalspanelplaceholder_changelist"
        )
        response = client.get(changelist_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.url)

    def test_non_staff_user_cannot_access_admin_signals_panel(self):
        """Test that non-staff users cannot access the Panel through admin."""
        user = User.objects.create_user(
            username="regular_user", password="testpass123", is_staff=False
        )

        client = Client()
        client.force_login(user)

        changelist_url = reverse(
            "admin:dj_signals_panel_signalspanelplaceholder_changelist"
        )
        response = client.get(changelist_url)

        self.assertIn(response.status_code, [302, 403])
