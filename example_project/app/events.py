"""
Extra signal module used by tests to verify the SIGNAL_MODULES config option.

This file is intentionally named 'events.py' (not 'signals.py') so the panel
does not discover it automatically through its installed-app scan. It must be
explicitly listed in DJ_SIGNALS_PANEL_SETTINGS["SIGNAL_MODULES"] to appear.
"""

from django.dispatch import Signal

user_invited = Signal()
export_completed = Signal()
