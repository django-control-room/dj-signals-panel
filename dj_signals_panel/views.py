import csv
import io
from dataclasses import asdict

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.contrib import admin
from django.http import Http404, JsonResponse, HttpResponse

from .conf import get_config, get_css_context
from .utils import SignalListInterface, SignalDetailInterface


@staff_member_required
def index(request):
    """Display panel dashboard with signal list."""
    interface = SignalListInterface()

    search_query = request.GET.get("q", "").strip()
    category_filter = request.GET.get("category", "").strip()

    if search_query:
        signals = interface.search_signals(search_query)
    else:
        signals = interface.get_signal_list()

    if category_filter:
        signals = [s for s in signals if s.category == category_filter]

    stats = interface.get_stats()
    grouped = interface.get_grouped_signals()
    available_categories = sorted(grouped.keys())

    context = admin.site.each_context(request)
    context.update(get_css_context())
    context.update(
        {
            "title": "Dj Signals Panel",
            "signals": signals,
            "stats": stats,
            "grouped_signals": grouped,
            "search_query": search_query,
            "category_filter": category_filter,
            "available_categories": available_categories,
            "total_displayed": len(signals),
        }
    )
    return render(request, "admin/dj_signals_panel/index.html", context)


@staff_member_required
def signal_detail(request, signal_id):
    """Display detailed information about a specific signal."""
    interface = SignalDetailInterface(signal_id)
    detail = interface.get_signal_detail()

    if detail is None:
        raise Http404("Signal not found")

    context = admin.site.each_context(request)
    context.update(get_css_context())
    context.update(
        {
            "title": f"Signal: {detail.name}",
            "signal": detail,
            "receivers": detail.receivers,
        }
    )
    return render(request, "admin/dj_signals_panel/detail.html", context)
