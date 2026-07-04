from django import template

register = template.Library()

# the original dcr-badge colors
_DCR_VARIANTS = (
    "",
    "success",
    "warning",
    "danger",
    "info",
    "muted",
    "purple",
    "indigo",
)

# the extra colors defined in styles.css just for the signals panel
_EXTRA_VARIANTS = (
    "teal",
    "pink",
    "orange",
    "cyan",
    "lime",
    "rose",
    "brown",
    "slate",
    "emerald",
    "sky",
    "violet",
    "fuchsia",
    "yellow",
    "red",
    "green",
    "blue",
    "amber",
    "gold",
    "maroon",
    "navy",
    "olive",
    "coral",
    "mint",
    "plum",
)
_ALL_VARIANTS = _DCR_VARIANTS + _EXTRA_VARIANTS

# Built-in Django signals (post_save, pre_delete, request_started, ...) have
# no owning app, so SignalUtils.module_to_app_label() falls back to the
# literal app_label "django". Pin it to the green/success variant so
# framework signals are instantly recognizable regardless of the hash.
_DJANGO_APP_LABEL = "django"


@register.filter
def dj_signals_panel_badge_variant(app_label: str) -> str:
    """
    Map an app label to a stable badge CSS class.

    Uses a simple character-sum hash so the same app label always maps to
    the same variant, giving each app a consistent colour across the panel.
    The "django" pseudo-app is pinned to green rather than hashed.
    """
    if app_label == _DJANGO_APP_LABEL:
        return "dcr-badge dcr-badge--success"

    index = sum(ord(c) for c in app_label) % len(_ALL_VARIANTS)
    variant = _ALL_VARIANTS[index]

    if variant in _DCR_VARIANTS:
        return f"dcr-badge dcr-badge--{variant}" if variant else "dcr-badge"
    return f"dcr-badge dj-signals-panel-badge--{variant}"
