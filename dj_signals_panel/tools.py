"""
MCP-facing introspection tools for dj-signals-panel.

Pure, read-only queries over the same signal-discovery machinery that backs
the panel's own views (see data.py). These are the primitives an agent needs
to answer "what signals exist", "who's listening", "what fires for this
model", and "where is this receiver defined" without grepping the codebase.
"""

from __future__ import annotations

import importlib
import inspect

from dj_control_room_base.core.panel_tool import (
    PanelToolContext,
    PanelToolResult,
    ToolRegistry,
)

# Django's built-in model lifecycle signals: the only signals Django itself
# guarantees to `.send(sender=ModelClass, ...)` for every model. A receiver
# connected to one of these with no sender filter genuinely fires for *every*
# model save/init/delete, so it's safe to surface as a "catch_all" match in
# find_signal_by_sender. The same isn't true for arbitrary custom signals —
# a catch-all receiver there only fires when someone calls `.send()`, which
# may have nothing to do with the model being asked about.
_MODEL_LIFECYCLE_SIGNALS = {
    ("django.db.models.signals", "pre_init"),
    ("django.db.models.signals", "post_init"),
    ("django.db.models.signals", "pre_save"),
    ("django.db.models.signals", "post_save"),
    ("django.db.models.signals", "pre_delete"),
    ("django.db.models.signals", "post_delete"),
}

registry = ToolRegistry()


@registry.register(
    name="list_signals",
    scope="introspect",
    description=(
        "List every signal Dj Signals Panel can see (Django built-ins "
        "and app-defined), with receiver counts and any senders "
        "receivers are bound to."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "app_label": {
                "type": "string",
                "description": "Filter to signals owned by this app label (e.g. 'app').",
            },
            "query": {
                "type": "string",
                "description": "Case-insensitive substring filter over the signal's name and dotted id.",
            },
        },
    },
)
def handle_list_signals(ctx: PanelToolContext) -> PanelToolResult:
    """List every signal DCR can see (built-in + app-defined), with bound senders."""
    from .data import SignalUtils

    app_label = (ctx.inputs.get("app_label") or "").strip()
    query = (ctx.inputs.get("query") or "").strip().lower()

    items = []
    for sig in SignalUtils.discover_all():
        if app_label and sig.app_label != app_label:
            continue
        if query and query not in sig.name.lower() and query not in sig.signal_id.lower():
            continue

        receivers = sig.receivers
        senders = sorted({r.sender for r in receivers if r.sender})

        items.append(
            {
                "signal_id": sig.signal_id,
                "name": sig.name,
                "module": sig.module,
                "app_label": sig.app_label,
                "receiver_count": len(receivers),
                "senders": senders,
                "providing_args": sig.providing_args,
            }
        )

    items.sort(key=lambda item: item["signal_id"])

    return PanelToolResult(
        success=True,
        message=f"{len(items)} signal(s) found.",
        data={"signals": items},
    )


@registry.register(
    name="get_receivers",
    scope="introspect",
    description=(
        "List the receivers connected to a signal: dotted path, "
        "dispatch_uid, weak/strong ref, and sender filter."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "signal": {
                "type": "string",
                "description": "Dotted signal id, e.g. 'app.signals.order_confirmed' or 'django.db.models.signals.post_save'.",
            },
        },
        "required": ["signal"],
    },
)
def handle_get_receivers(ctx: PanelToolContext) -> PanelToolResult:
    """List receivers connected to a signal: dotted path, dispatch_uid, ref type, sender."""
    from .data import DiscoveredSignal

    signal_id = (ctx.inputs.get("signal") or "").strip()
    if not signal_id:
        return PanelToolResult(
            success=False,
            message="'signal' is required (dotted signal id, e.g. 'app.signals.order_confirmed').",
        )

    signal = DiscoveredSignal.from_id(signal_id)
    if signal is None:
        return PanelToolResult(
            success=False, message=f"No signal found for id '{signal_id}'."
        )

    receivers = [_receiver_to_dict(r) for r in signal.receivers]

    return PanelToolResult(
        success=True,
        message=f"{len(receivers)} receiver(s) connected to '{signal_id}'.",
        data={"signal_id": signal_id, "receivers": receivers},
    )


@registry.register(
    name="find_signal_by_sender",
    scope="introspect",
    description=(
        "Reverse lookup: given a model, find every signal/receiver "
        "that fires for it (e.g. 'what fires when Order is saved')."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "description": "Model reference: 'app_label.ModelName' (unambiguous) or a bare 'ModelName'.",
            },
        },
        "required": ["model"],
    },
)
def handle_find_signal_by_sender(ctx: PanelToolContext) -> PanelToolResult:
    """Reverse lookup: which signals/receivers fire for a given model (e.g. 'what fires when Order is saved')."""
    from .data import SignalUtils

    model_ref = (ctx.inputs.get("model") or "").strip()
    if not model_ref:
        return PanelToolResult(
            success=False,
            message="'model' is required (e.g. 'Order' or 'myapp.Order').",
        )

    model, error = _resolve_model(model_ref)
    if error:
        return PanelToolResult(success=False, message=error)

    matches = []
    for sig in SignalUtils.discover_all():
        is_lifecycle_signal = (sig.module, sig.name) in _MODEL_LIFECYCLE_SIGNALS
        signal_matches = []

        for r in sig.receivers:
            sender_model = r.sender_model
            if sender_model is model:
                match_type = "sender"
            elif sender_model is None and is_lifecycle_signal:
                match_type = "catch_all"
            else:
                continue

            entry = _receiver_to_dict(r)
            entry["match_type"] = match_type
            signal_matches.append(entry)

        if signal_matches:
            matches.append(
                {
                    "signal_id": sig.signal_id,
                    "name": sig.name,
                    "module": sig.module,
                    "receivers": signal_matches,
                }
            )

    return PanelToolResult(
        success=True,
        message=f"{len(matches)} signal(s) fire for {model._meta.label}.",
        data={"model": model._meta.label, "signals": matches},
    )


@registry.register(
    name="inspect_receiver",
    scope="introspect",
    description=(
        "Resolve a receiver's dotted path to its source file/line "
        "(and any signals it's currently connected to), so an agent "
        "can jump straight to the function instead of grepping."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "dotted_path": {
                "type": "string",
                "description": "Dotted path to the receiver function, e.g. 'app.handlers.on_order_confirmed'.",
            },
        },
        "required": ["dotted_path"],
    },
)
def handle_inspect_receiver(ctx: PanelToolContext) -> PanelToolResult:
    """Resolve a dotted path to its source location so an agent can jump straight to it."""
    dotted_path = (ctx.inputs.get("dotted_path") or "").strip()
    if not dotted_path:
        return PanelToolResult(
            success=False,
            message="'dotted_path' is required, e.g. 'app.handlers.on_order_confirmed'.",
        )

    obj, resolved_module = _resolve_dotted(dotted_path)
    if obj is None:
        return PanelToolResult(
            success=False,
            message=f"Could not resolve '{dotted_path}' to an importable object.",
        )

    if not callable(obj):
        return PanelToolResult(
            success=False,
            message=f"'{dotted_path}' resolved to a non-callable {type(obj).__name__}.",
        )

    unwrapped = inspect.unwrap(obj, stop=lambda f: not hasattr(f, "__wrapped__"))

    try:
        source_file = inspect.getfile(unwrapped)
    except (TypeError, OSError):
        source_file = None

    try:
        lines, source_line = inspect.getsourcelines(unwrapped)
    except (TypeError, OSError):
        lines, source_line = None, None

    source_preview = None
    if lines is not None and ctx.config.get_settings("SHOW_SOURCE"):
        max_lines = 20
        source_preview = "".join(lines[:max_lines])
        if len(lines) > max_lines:
            source_preview += f"\n    # ... ({len(lines) - max_lines} more lines)"

    data = {
        "dotted_path": dotted_path,
        "resolved_module": resolved_module,
        "qualname": getattr(obj, "__qualname__", getattr(obj, "__name__", dotted_path)),
        "module": getattr(obj, "__module__", resolved_module),
        "source_file": source_file,
        "source_line": source_line,
        "source_preview": source_preview,
        "docstring": inspect.getdoc(obj),
        "connected_signals": _find_connected_signals(obj),
    }

    location = f" at {source_file}:{source_line}" if source_file else ""
    return PanelToolResult(
        success=True,
        message=f"Resolved '{dotted_path}'{location}.",
        data=data,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _receiver_to_dict(receiver) -> dict:
    sender_model = receiver.sender_model
    return {
        "function_name": receiver.function_name,
        "dotted_path": receiver.dotted_path,
        "module": receiver.module,
        "dispatch_uid": receiver.dispatch_uid,
        "ref_type": "weak" if receiver.is_weak else "strong",
        "is_async": receiver.is_async,
        "sender": receiver.sender,
        "sender_model": sender_model._meta.label if sender_model else None,
        "source_file": receiver.source_file,
        "source_line": receiver.source_line,
    }


def _resolve_model(model_ref: str):
    """
    Resolve a user-supplied model reference to an installed Model class.

    Accepts "app_label.ModelName" (unambiguous) or a bare "ModelName" (looked
    up by class name across every installed app; ambiguous if more than one
    app has a model with that name).
    """
    from django.apps import apps

    if "." in model_ref:
        app_label, _, model_name = model_ref.rpartition(".")
        app_label = app_label.rsplit(".", 1)[-1]
        try:
            return apps.get_model(app_label, model_name), None
        except LookupError:
            pass

    matches = [m for m in apps.get_models() if m.__name__.lower() == model_ref.lower()]
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        labels = ", ".join(sorted(m._meta.label for m in matches))
        return (
            None,
            f"Ambiguous model name '{model_ref}'. Matches: {labels}. "
            "Use 'app_label.ModelName' instead.",
        )
    return None, f"No installed model found matching '{model_ref}'."


def _resolve_dotted(dotted_path: str):
    """
    Resolve a dotted path to an object, trying the longest importable module
    prefix first and walking the remainder via getattr (handles both plain
    module-level functions and nested class methods).
    """
    parts = dotted_path.split(".")
    for i in range(len(parts) - 1, 0, -1):
        module_path = ".".join(parts[:i])
        try:
            mod = importlib.import_module(module_path)
        except Exception:
            continue

        obj = mod
        try:
            for attr in parts[i:]:
                obj = getattr(obj, attr)
        except AttributeError:
            continue

        return obj, module_path

    return None, None


def _find_connected_signals(obj) -> list[dict]:
    """Return every signal/receiver pairing where `obj` is the live receiver."""
    from .data import SignalUtils

    underlying = getattr(obj, "__func__", obj)
    matches = []
    for sig in SignalUtils.discover_all():
        for r in sig.receivers:
            if r.func is obj or r.func is underlying:
                matches.append(
                    {
                        "signal_id": sig.signal_id,
                        "dispatch_uid": r.dispatch_uid,
                        "sender": r.sender,
                    }
                )
    return matches
