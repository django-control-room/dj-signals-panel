from __future__ import annotations

import importlib
import inspect
import weakref
from dataclasses import dataclass, field

from django.dispatch import Signal as DjangoSignal

from .conf import get_config


@dataclass
class ReceiverInfo:
    """Template-facing data for a single receiver."""

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
    """Template-facing data for one row in the signal list."""

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
    """Aggregate statistics for the list-page stats card."""

    total_signals: int
    total_receivers: int
    signals_without_receivers: int
    most_connected_signal: str | None
    most_connected_count: int
    category_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class SignalDetail:
    """Template-facing data for the signal detail page."""

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


class Receiver:
    """
    Represents a single receiver registered to a Django signal.

    Wraps a raw entry from signal_obj.receivers, handling both the legacy
    2-tuple (lookup_key, receiver_ref) format and the Django 5.1+ 4-tuple
    (lookup_key, receiver_ref, sender_ref, is_async) format.
    """

    def __init__(self, entry: tuple) -> None:
        if len(entry) < 2:
            raise ValueError(f"Unexpected receiver entry format: {entry!r}")
        self._lookup_key = entry[0]
        self._receiver_ref = entry[1]
        self.is_async: bool = bool(entry[3]) if len(entry) > 3 else False
        self._func = self._resolve_func()

    def _resolve_func(self) -> object | None:
        ref = self._receiver_ref
        if isinstance(ref, weakref.ref):
            return ref()
        return ref

    @property
    def is_alive(self) -> bool:
        return self._func is not None

    @property
    def function_name(self) -> str:
        return getattr(self._func, "__name__", str(self._func))

    @property
    def qualname(self) -> str:
        return getattr(self._func, "__qualname__", "")

    @property
    def module(self) -> str:
        return getattr(self._func, "__module__", "")

    @property
    def _unwrapped(self):
        return inspect.unwrap(self._func, stop=lambda f: not hasattr(f, "__wrapped__"))

    @property
    def source_file(self) -> str | None:
        try:
            return inspect.getfile(self._unwrapped)
        except (TypeError, OSError):
            return None

    @property
    def source_line(self) -> int | None:
        try:
            _, line = inspect.getsourcelines(self._unwrapped)
            return line
        except (TypeError, OSError):
            return None

    def get_source_preview(self, max_lines: int = 20) -> str | None:
        try:
            lines, _ = inspect.getsourcelines(self._unwrapped)
            preview = "".join(lines[:max_lines])
            if len(lines) > max_lines:
                preview += f"\n    # ... ({len(lines) - max_lines} more lines)"
            return preview
        except (TypeError, OSError):
            return None

    @property
    def sender(self) -> str | None:
        key = self._lookup_key
        if not isinstance(key, tuple) or len(key) < 2:
            return None
        sender_id = key[1]
        if sender_id == id(None):
            return None
        return f"<sender id={sender_id}>"

    @property
    def dispatch_uid(self) -> str | None:
        key = self._lookup_key
        if not isinstance(key, tuple) or len(key) < 1:
            return None
        uid = key[0]
        return uid if isinstance(uid, str) else None

    def to_info(self) -> ReceiverInfo:
        """Return the template-facing DTO for this receiver."""
        return ReceiverInfo(
            function_name=self.function_name,
            qualname=self.qualname,
            module=self.module,
            source_file=self.source_file,
            source_line=self.source_line,
            sender=self.sender,
            dispatch_uid=self.dispatch_uid,
            source_preview=self.get_source_preview(),
        )


class DiscoveredSignal:
    """
    Represents a Django signal discovered by the panel.

    Wraps a django.dispatch.Signal instance alongside the metadata needed
    to describe it: its dotted id, name, module, category, and app label.
    """

    def __init__(
        self,
        signal_id: str,
        signal_obj: DjangoSignal,
        name: str,
        module: str,
        category: str,
        app_label: str | None,
    ) -> None:
        self.signal_id = signal_id
        self._signal_obj = signal_obj
        self.name = name
        self.module = module
        self.category = category
        self.app_label = app_label

    @classmethod
    def from_id(cls, signal_id: str) -> DiscoveredSignal | None:
        """
        Resolve a dotted signal_id string to a DiscoveredSignal.

        Returns None if the module cannot be imported or the attribute is not
        a Django Signal instance.
        """
        parts = signal_id.rsplit(".", 1)
        if len(parts) != 2:
            return None
        module_path, attr_name = parts
        try:
            mod = importlib.import_module(module_path)
            obj = getattr(mod, attr_name, None)
            if not isinstance(obj, DjangoSignal):
                return None
        except Exception:
            return None
        category = CATEGORY_MAP.get(module_path, "custom")
        app_label = (
            None
            if category != "custom"
            else SignalUtils.module_to_app_label(module_path)
        )
        return cls(
            signal_id=signal_id,
            signal_obj=obj,
            name=attr_name,
            module=module_path,
            category=category,
            app_label=app_label,
        )

    @classmethod
    def from_obj(
        cls,
        signal_obj: DjangoSignal,
        signal_id: str,
        name: str,
        module_path: str,
        category: str,
        app_label: str | None,
    ) -> DiscoveredSignal:
        """Construct directly from an already-resolved Signal object."""
        return cls(
            signal_id=signal_id,
            signal_obj=signal_obj,
            name=name,
            module=module_path,
            category=category,
            app_label=app_label,
        )

    @property
    def receivers(self) -> list[Receiver]:
        """All live receivers currently connected to this signal."""
        result = []
        for entry in self._signal_obj.receivers:
            if len(entry) < 2:
                continue
            try:
                r = Receiver(entry)
                if r.is_alive:
                    result.append(r)
            except Exception:
                continue
        return result

    @property
    def receiver_count(self) -> int:
        return len(self._signal_obj.receivers)

    @property
    def providing_args(self) -> list[str]:
        return list(getattr(self._signal_obj, "providing_args", []) or [])

    def to_summary(self) -> SignalSummary:
        """Return the template-facing summary DTO."""
        return SignalSummary(
            signal_id=self.signal_id,
            name=self.name,
            module=self.module,
            category=self.category,
            app_label=self.app_label,
            receiver_count=self.receiver_count,
            providing_args=self.providing_args,
        )

    def to_detail(self) -> SignalDetail:
        """Return the template-facing detail DTO with full receiver list."""
        return SignalDetail(
            signal_id=self.signal_id,
            name=self.name,
            module=self.module,
            category=self.category,
            app_label=self.app_label,
            providing_args=self.providing_args,
            receivers=[r.to_info() for r in self.receivers],
        )


class SignalUtils:
    """Handles signal discovery, stats computation, and shared helpers."""

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

    @staticmethod
    def discover_builtin() -> list[DiscoveredSignal]:
        """Return all known built-in Django signals."""
        results: list[DiscoveredSignal] = []
        for module_path, signal_names in BUILTIN_SIGNALS.items():
            try:
                mod = importlib.import_module(module_path)
            except ImportError:
                continue
            category = CATEGORY_MAP.get(module_path, "other")
            for name in signal_names:
                signal_obj = getattr(mod, name, None)
                if signal_obj is None or not isinstance(signal_obj, DjangoSignal):
                    continue
                results.append(
                    DiscoveredSignal.from_obj(
                        signal_obj,
                        f"{module_path}.{name}",
                        name,
                        module_path,
                        category,
                        None,
                    )
                )
        return results

    @staticmethod
    def discover_custom() -> list[DiscoveredSignal]:
        """
        Return all custom signals found across installed apps.

        Scans every app's .signals and .handlers modules automatically,
        plus any extra modules listed in SIGNAL_MODULES config.
        """
        builtin_ids = {
            f"{mod}.{name}" for mod, names in BUILTIN_SIGNALS.items() for name in names
        }

        modules_to_scan = list(SignalUtils.get_signal_modules())

        for app_config in SignalUtils.get_installed_app_configs():
            for suffix in ("signals", "handlers"):
                module_path = f"{app_config.name}.{suffix}"
                if module_path not in modules_to_scan:
                    modules_to_scan.append(module_path)

        results: list[DiscoveredSignal] = []
        seen_ids: set[str] = set()

        for module_path in modules_to_scan:
            try:
                mod = importlib.import_module(module_path)
            except Exception:
                continue

            app_label = SignalUtils.module_to_app_label(module_path)

            for attr_name in dir(mod):
                obj = getattr(mod, attr_name, None)
                if not isinstance(obj, DjangoSignal):
                    continue
                signal_id = f"{module_path}.{attr_name}"
                if signal_id in builtin_ids or signal_id in seen_ids:
                    continue
                seen_ids.add(signal_id)
                results.append(
                    DiscoveredSignal.from_obj(
                        obj, signal_id, attr_name, module_path, "custom", app_label
                    )
                )

        return results

    @staticmethod
    def discover_all() -> list[DiscoveredSignal]:
        """Return all built-in and custom signals."""
        return SignalUtils.discover_builtin() + SignalUtils.discover_custom()

    @staticmethod
    def compute_stats(signals: list[SignalSummary]) -> SignalStats:
        """Compute aggregate statistics from a list of signal summaries."""
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
