from __future__ import annotations

import importlib
import inspect
import weakref
from dataclasses import dataclass, field

from django.dispatch import Signal

from .conf import get_config


@dataclass
class ReceiverInfo:
    """A single receiver connected to a signal."""

    function_name: str
    qualname: str
    module: str
    source_file: str | None
    source_line: int | None
    sender: str | None
    dispatch_uid: str | None
    source_preview: str | None = None


@dataclass
class SignalSummary:
    """One row in the signal list table."""

    signal_id: str
    name: str
    module: str
    category: str
    app_label: str | None
    receiver_count: int
    providing_args: list[str] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return self.receiver_count == 0


@dataclass
class SignalStats:
    """Summary statistics card for the list page."""

    total_signals: int
    total_receivers: int
    signals_without_receivers: int
    most_connected_signal: str | None
    most_connected_count: int
    category_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class SignalDetail:
    """Full signal info for the detail page."""

    signal_id: str
    name: str
    module: str
    category: str
    app_label: str | None
    providing_args: list[str] = field(default_factory=list)
    receivers: list[ReceiverInfo] = field(default_factory=list)


BUILTIN_SIGNALS: dict[str, list[str]] = {
    "django.db.models.signals": [
        "pre_init",
        "post_init",
        "pre_save",
        "post_save",
        "pre_delete",
        "post_delete",
        "m2m_changed",
    ],
    "django.core.signals": [
        "request_started",
        "request_finished",
        "got_request_exception",
        "setting_changed",
    ],
    "django.test.signals": [
        "template_rendered",
    ],
    "django.db.backends.signals": [
        "connection_created",
    ],
}

CATEGORY_MAP: dict[str, str] = {
    "django.db.models.signals": "model",
    "django.core.signals": "request",
    "django.test.signals": "test",
    "django.db.backends.signals": "management",
}
