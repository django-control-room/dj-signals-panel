from django import template

register = template.Library()

_NUM_COLORS = 16


@register.filter
def dj_signals_panel_add_badge_class(app_label: str) -> str:
    """
    Map an app label to a stable badge CSS class (dj-sp-badge-0 … dj-sp-badge-7).
    """
    index = sum(ord(c) for c in app_label) % _NUM_COLORS
    return f"dj-sp-badge dj-sp-badge-{index}"
