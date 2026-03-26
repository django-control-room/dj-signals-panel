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


class SignalUtils:
    """
    Util class to be used in interface classes below. Much of the common logic
    around signal discovery and configuration is shared here.
    """

    @staticmethod
    def get_signal_modules() -> list[str]:
        return get_config("SIGNAL_MODULES") or []

    @staticmethod
    def get_installed_app_configs():
        from django.apps import apps

        return apps.get_app_configs()

    @staticmethod
    def module_to_app_label(module_path: str) -> str | None:
        from django.apps import apps

        parts = module_path.split(".")
        for i in range(len(parts), 0, -1):
            candidate = ".".join(parts[:i])
            try:
                return apps.get_app_config(candidate.split(".")[-1]).label
            except LookupError:
                continue
        return None

    # -- signal resolution ----------------------------------------------------

    @staticmethod
    def resolve_signal(signal_id: str) -> Signal | None:
        """Import the module and retrieve the Signal attribute."""
        parts = signal_id.rsplit(".", 1)
        if len(parts) != 2:
            return None
        module_path, attr_name = parts
        try:
            mod = importlib.import_module(module_path)
            obj = getattr(mod, attr_name, None)
            return obj if isinstance(obj, Signal) else None
        except (ImportError, Exception):
            return None

    @staticmethod
    def signal_to_summary(
        signal_obj: Signal,
        signal_id: str,
        name: str,
        module_path: str,
        category: str,
        app_label: str | None,
    ) -> SignalSummary:
        providing_args = list(getattr(signal_obj, "providing_args", []) or [])
        return SignalSummary(
            signal_id=signal_id,
            name=name,
            module=module_path,
            category=category,
            app_label=app_label,
            receiver_count=len(signal_obj.receivers),
            providing_args=providing_args,
        )

    # -- receiver extraction --------------------------------------------------

    @staticmethod
    def resolve_receiver(receiver_ref) -> object | None:
        if isinstance(receiver_ref, weakref.ref):
            return receiver_ref()
        return receiver_ref

    @staticmethod
    def get_source_location(func) -> tuple[str | None, int | None]:
        unwrapped = inspect.unwrap(func, stop=lambda f: not hasattr(f, "__wrapped__"))
        try:
            source_file = inspect.getfile(unwrapped)
        except (TypeError, OSError):
            source_file = None
        try:
            _, source_line = inspect.getsourcelines(unwrapped)
        except (TypeError, OSError):
            source_line = None
        return source_file, source_line

    @staticmethod
    def get_source_preview(func, max_lines: int = 20) -> str | None:
        unwrapped = inspect.unwrap(func, stop=lambda f: not hasattr(f, "__wrapped__"))
        try:
            lines, _ = inspect.getsourcelines(unwrapped)
            preview = "".join(lines[:max_lines])
            if len(lines) > max_lines:
                preview += f"\n    # ... ({len(lines) - max_lines} more lines)"
            return preview
        except (TypeError, OSError):
            return None

    @staticmethod
    def resolve_sender(lookup_key) -> str | None:
        if not isinstance(lookup_key, tuple) or len(lookup_key) < 2:
            return None
        sender_id = lookup_key[1]
        if sender_id == id(None):
            return None
        return f"<sender id={sender_id}>"

    @staticmethod
    def resolve_dispatch_uid(lookup_key) -> str | None:
        if not isinstance(lookup_key, tuple) or len(lookup_key) < 1:
            return None
        uid = lookup_key[0]
        if isinstance(uid, str):
            return uid
        return None

    @staticmethod
    def extract_receivers(signal_obj: Signal) -> list[ReceiverInfo]:
        receivers: list[ReceiverInfo] = []
        for lookup_key, receiver_ref in signal_obj.receivers:
            receiver_func = SignalUtils.resolve_receiver(receiver_ref)
            if receiver_func is None:
                continue

            source_file, source_line = SignalUtils.get_source_location(receiver_func)
            sender = SignalUtils.resolve_sender(lookup_key)
            dispatch_uid = SignalUtils.resolve_dispatch_uid(lookup_key)
            source_preview = SignalUtils.get_source_preview(receiver_func)

            receivers.append(
                ReceiverInfo(
                    function_name=getattr(
                        receiver_func, "__name__", str(receiver_func)
                    ),
                    qualname=getattr(receiver_func, "__qualname__", ""),
                    module=getattr(receiver_func, "__module__", ""),
                    source_file=source_file,
                    source_line=source_line,
                    sender=sender,
                    dispatch_uid=dispatch_uid,
                    source_preview=source_preview,
                )
            )
        return receivers


# ---------------------------------------------------------------------------
# SignalListInterface – serves the index view
# ---------------------------------------------------------------------------


class SignalListInterface(SignalUtils):
    """
    Interface for the signal list (index) page.

    Discovers all Django signals (built-in and custom) and returns
    summary-level data suitable for a list/table view.
    """

    def __init__(self):
        self._signals: list[SignalSummary] | None = None

    # -- public API ----------------------------------------------------------

    def get_signal_list(self) -> list[SignalSummary]:
        """All discovered signals with summary metadata."""
        if self._signals is None:
            self._signals = (
                self._discover_builtin_signals() + self._discover_custom_signals()
            )
        return self._signals

    def get_grouped_signals(self) -> dict[str, list[SignalSummary]]:
        """Signals grouped by category."""
        grouped: dict[str, list[SignalSummary]] = {}
        for sig in self.get_signal_list():
            grouped.setdefault(sig.category, []).append(sig)
        return grouped

    def search_signals(self, query: str) -> list[SignalSummary]:
        """Filter signals by name, module, or category."""
        q = query.lower()
        return [
            s
            for s in self.get_signal_list()
            if (
                q in s.name.lower()
                or q in s.module.lower()
                or q in s.signal_id.lower()
                or q in s.category.lower()
            )
        ]

    def get_stats(self) -> SignalStats:
        """Aggregate statistics for the stats card."""
        signals = self.get_signal_list()
        if not signals:
            return SignalStats(
                total_signals=0,
                total_receivers=0,
                signals_without_receivers=0,
                most_connected_signal=None,
                most_connected_count=0,
            )

        total_receivers = sum(s.receiver_count for s in signals)
        without_receivers = sum(1 for s in signals if s.receiver_count == 0)
        most_connected = max(signals, key=lambda s: s.receiver_count)

        category_counts: dict[str, int] = {}
        for s in signals:
            category_counts[s.category] = category_counts.get(s.category, 0) + 1

        return SignalStats(
            total_signals=len(signals),
            total_receivers=total_receivers,
            signals_without_receivers=without_receivers,
            most_connected_signal=most_connected.name
            if most_connected.receiver_count > 0
            else None,
            most_connected_count=most_connected.receiver_count,
            category_counts=category_counts,
        )

    # -- private helpers -----------------------------------------------------

    def _discover_builtin_signals(self) -> list[SignalSummary]:
        results: list[SignalSummary] = []
        for module_path, signal_names in BUILTIN_SIGNALS.items():
            try:
                mod = importlib.import_module(module_path)
            except ImportError:
                continue
            category = CATEGORY_MAP.get(module_path, "other")
            for name in signal_names:
                signal_obj = getattr(mod, name, None)
                if signal_obj is None or not isinstance(signal_obj, Signal):
                    continue
                results.append(
                    self.signal_to_summary(
                        signal_obj,
                        f"{module_path}.{name}",
                        name,
                        module_path,
                        category,
                        None,
                    )
                )
        return results

    def _discover_custom_signals(self) -> list[SignalSummary]:
        builtin_ids = {
            f"{mod}.{name}" for mod, names in BUILTIN_SIGNALS.items() for name in names
        }

        modules_to_scan = list(self.get_signal_modules())

        for app_config in self.get_installed_app_configs():
            for suffix in ("signals", "handlers"):
                module_path = f"{app_config.name}.{suffix}"
                if module_path not in modules_to_scan:
                    modules_to_scan.append(module_path)

        results: list[SignalSummary] = []
        seen_ids: set[str] = set()

        for module_path in modules_to_scan:
            try:
                mod = importlib.import_module(module_path)
            except (ImportError, Exception):
                continue

            app_label = self.module_to_app_label(module_path)

            for attr_name in dir(mod):
                obj = getattr(mod, attr_name, None)
                if not isinstance(obj, Signal):
                    continue
                signal_id = f"{module_path}.{attr_name}"
                if signal_id in builtin_ids or signal_id in seen_ids:
                    continue
                seen_ids.add(signal_id)
                results.append(
                    self.signal_to_summary(
                        obj, signal_id, attr_name, module_path, "custom", app_label
                    )
                )

        return results


# ---------------------------------------------------------------------------
# SignalDetailInterface – serves the detail view
# ---------------------------------------------------------------------------


class SignalDetailInterface(SignalUtils):
    """
    Interface for the signal detail page.

    Given a signal_id, resolves the signal and extracts full
    receiver information including source locations.
    """

    def __init__(self, signal_id: str):
        self.signal_id = signal_id

    # -- public API ----------------------------------------------------------

    def get_signal_detail(self) -> SignalDetail | None:
        """Full signal info with all receivers. Returns None if not found."""
        signal_obj = self.resolve_signal(self.signal_id)
        if signal_obj is None:
            return None

        parts = self.signal_id.rsplit(".", 1)
        module_path = parts[0] if len(parts) == 2 else ""
        name = parts[1] if len(parts) == 2 else self.signal_id

        category = CATEGORY_MAP.get(module_path, "custom")
        app_label = (
            None if category != "custom" else self.module_to_app_label(module_path)
        )

        return SignalDetail(
            signal_id=self.signal_id,
            name=name,
            module=module_path,
            category=category,
            app_label=app_label,
            providing_args=list(getattr(signal_obj, "providing_args", []) or []),
            receivers=self.extract_receivers(signal_obj),
        )
