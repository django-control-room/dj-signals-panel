from __future__ import annotations

import importlib
import inspect
import weakref
from dataclasses import dataclass, field

from django.dispatch import Signal as DjangoSignal

from .conf import panel_config


def resolve_sender_model(sender_id: int):
    """
    Best-effort resolution of a stored sender id() back to the actual Model
    class.

    Django's dispatcher only ever stores id(sender) in its lookup key, never
    the sender itself, so the original object can't be retrieved directly.
    Most real-world senders are Model classes registered with a receiver via
    `sender=SomeModel`. Returns None if no installed model's id() matches
    (e.g. the sender isn't a Model at all).
    """
    from django.apps import apps

    for model in apps.get_models():
        if id(model) == sender_id:
            return model

    return None


def _resolve_sender_label(sender_id: int) -> str:
    """Best-effort resolution of a stored sender id() back to a readable label."""
    model = resolve_sender_model(sender_id)
    return model.__name__ if model is not None else "Specific sender"


@dataclass
class ReceiverInfo:
    """Template-facing data for a single receiver."""

    function_name: str
    qualname: str
    module: str
    source_file: str | None
    source_line: int | None
    sender: str | None
    source_preview: str | None = None


@dataclass
class SignalSummary:
    """Template-facing data for one row in the signal list."""

    signal_id: str
    name: str
    module: str
    app_label: str
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
    app_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class SignalDetail:
    """Template-facing data for the signal detail page."""

    signal_id: str
    name: str
    module: str
    app_label: str
    providing_args: list[str] = field(default_factory=list)
    receivers: list[ReceiverInfo] = field(default_factory=list)


# Django's built-in signal modules are not attached to a registered app config,
# so they cannot be found by scanning installed apps. We seed the scan with
# their module paths only — individual signal names are discovered via dir().
_DJANGO_SIGNAL_MODULES: list[str] = [
    "django.db.models.signals",
    "django.core.signals",
    "django.test.signals",
    "django.db.backends.signals",
]


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
    def func(self) -> object | None:
        """The resolved receiver callable (dereferenced from its weakref, if any)."""
        return self._func

    @property
    def dispatch_uid(self) -> str | None:
        """
        The dispatch_uid this receiver was connected with, if any.

        Django's lookup key is (dispatch_uid, sender_id) when dispatch_uid was
        provided, or (id(receiver), sender_id) otherwise. Since Django's own
        docs mandate dispatch_uid be a string, a string first element reliably
        distinguishes an explicit dispatch_uid from an auto-generated id().
        """
        key = self._lookup_key
        if isinstance(key, tuple) and len(key) >= 1 and isinstance(key[0], str):
            return key[0]
        return None

    @property
    def is_weak(self) -> bool:
        """Whether this receiver was connected with weak=True (Django's default)."""
        return isinstance(self._receiver_ref, weakref.ref)

    @property
    def dotted_path(self) -> str:
        """Best-effort importable-looking dotted path to the receiver function."""
        if self.module and self.qualname:
            return f"{self.module}.{self.qualname}"
        return self.function_name

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
        return _resolve_sender_label(sender_id)

    @property
    def sender_model(self):
        """
        The actual Model class this receiver is filtered to, or None if the
        receiver matches any sender (no sender filter was given at connect
        time) or the sender isn't a resolvable installed Model.
        """
        key = self._lookup_key
        if not isinstance(key, tuple) or len(key) < 2:
            return None
        sender_id = key[1]
        if sender_id == id(None):
            return None
        return resolve_sender_model(sender_id)

    def to_info(self) -> ReceiverInfo:
        """Return the template-facing DTO for this receiver."""
        return ReceiverInfo(
            function_name=self.function_name,
            qualname=self.qualname,
            module=self.module,
            source_file=self.source_file,
            source_line=self.source_line,
            sender=self.sender,
            source_preview=self.get_source_preview()
            if panel_config.get_settings("SHOW_SOURCE")
            else None,
        )


class DiscoveredSignal:
    """
    Represents a Django signal discovered by the panel.

    Wraps a django.dispatch.Signal instance alongside the metadata needed
    to describe it: its dotted id, name, module, and owning app label.
    """

    def __init__(
        self,
        signal_id: str,
        signal_obj: DjangoSignal,
        name: str,
        module: str,
        app_label: str,
    ) -> None:
        self.signal_id = signal_id
        self._signal_obj = signal_obj
        self.name = name
        self.module = module
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
        return cls(
            signal_id=signal_id,
            signal_obj=obj,
            name=attr_name,
            module=module_path,
            app_label=SignalUtils.module_to_app_label(module_path),
        )

    @classmethod
    def from_obj(
        cls,
        signal_obj: DjangoSignal,
        signal_id: str,
        name: str,
        module_path: str,
        app_label: str,
    ) -> DiscoveredSignal:
        """Construct directly from an already-resolved Signal object."""
        return cls(
            signal_id=signal_id,
            signal_obj=signal_obj,
            name=name,
            module=module_path,
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
            app_label=self.app_label,
            providing_args=self.providing_args,
            receivers=[r.to_info() for r in self.receivers],
        )


class SignalUtils:
    """Handles signal discovery, stats computation, and shared helpers."""

    @staticmethod
    def get_signal_modules() -> list[str]:
        return panel_config.get_settings("SIGNAL_MODULES") or []

    @staticmethod
    def get_installed_app_configs():
        from django.apps import apps

        return apps.get_app_configs()

    @staticmethod
    def module_to_app_label(module_path: str) -> str:
        """
        Return the Django app label that owns module_path.

        Falls back to the top-level package name when the module does not
        belong to a registered app (e.g. django.db.models.signals → "django").
        """
        from django.apps import apps

        parts = module_path.split(".")
        for i in range(len(parts), 0, -1):
            candidate = ".".join(parts[:i])
            try:
                return apps.get_app_config(candidate.split(".")[-1]).label
            except LookupError:
                continue
        return parts[0]

    @staticmethod
    def discover_all() -> list[DiscoveredSignal]:
        """
        Discover all signals: Django built-ins and app-defined signals.

        Scans:
        - _DJANGO_SIGNAL_MODULES: built-in Django signal module paths that
          are not reachable via the app config registry.
        - Every installed app's .signals and .handlers modules.
        - Any extra module paths from the SIGNAL_MODULES config.

        All modules are scanned the same way — dir() to find Signal instances.
        """
        modules_to_scan: list[str] = list(_DJANGO_SIGNAL_MODULES)

        for module_path in SignalUtils.get_signal_modules():
            if module_path not in modules_to_scan:
                modules_to_scan.append(module_path)

        for app_config in SignalUtils.get_installed_app_configs():
            module_path = f"{app_config.name}.signals"
            if module_path not in modules_to_scan:
                modules_to_scan.append(module_path)

        results: list[DiscoveredSignal] = []
        seen_object_ids: set[int] = set()

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
                # Deduplicate by Python object identity: a Signal imported into
                # multiple modules is the same object — only record it once,
                # using the module path from its first (canonical) encounter.
                if id(obj) in seen_object_ids:
                    continue
                seen_object_ids.add(id(obj))
                signal_id = f"{module_path}.{attr_name}"
                results.append(
                    DiscoveredSignal.from_obj(
                        obj, signal_id, attr_name, module_path, app_label
                    )
                )

        return results

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

        app_counts: dict[str, int] = {}
        for s in signals:
            app_counts[s.app_label] = app_counts.get(s.app_label, 0) + 1

        return SignalStats(
            total_signals=len(signals),
            total_receivers=total_receivers,
            signals_without_receivers=without_receivers,
            most_connected_signal=most_connected.name
            if most_connected.receiver_count > 0
            else None,
            most_connected_count=most_connected.receiver_count,
            app_counts=app_counts,
        )
