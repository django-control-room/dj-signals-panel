from django.shortcuts import render
from django.http import Http404

from .conf import panel_config
from .interfaces import SignalListInterface, SignalDetailInterface


@panel_config.permission_required("index")
def index(request):
    """Display panel dashboard with signal list."""
    interface = SignalListInterface()

    search_query = request.GET.get("q", "").strip()
    app_filter = request.GET.get("app", "").strip()

    if search_query:
        signals = interface.search_signals(search_query)
    else:
        signals = interface.get_signal_list()

    if app_filter:
        signals = [s for s in signals if s.app_label == app_filter]

    stats = interface.get_stats()
    grouped = interface.get_grouped_signals()
    signal_apps = sorted(grouped.keys())

    context = panel_config.get_context(
        request,
        title="Dj Signals Panel",
        dj_cr_show_source=panel_config.get_settings("SHOW_SOURCE"),
        signals=signals,
        stats=stats,
        grouped_signals=grouped,
        search_query=search_query,
        app_filter=app_filter,
        signal_apps=signal_apps,
        total_displayed=len(signals),
    )
    return render(request, "admin/dj_signals_panel/index.html", context)


@panel_config.permission_required("detail")
def signal_detail(request, signal_id):
    """Display detailed information about a specific signal."""
    interface = SignalDetailInterface(signal_id)
    detail = interface.get_signal_detail()

    if detail is None:
        raise Http404("Signal not found")

    context = panel_config.get_context(
        request,
        title=f"Signal: {detail.name}",
        dj_cr_show_source=panel_config.get_settings("SHOW_SOURCE"),
        signal=detail,
        receivers=detail.receivers,
    )
    return render(request, "admin/dj_signals_panel/detail.html", context)
