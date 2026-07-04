from dj_control_room_base.core import PanelPlugin


class SignalsPanel(PanelPlugin):
    name = "Signals Panel"
    description = "Monitor and debug Django signals"
    icon = "radio"
    icon_color = "indigo"
    features = [
        "Browse all registered Django signals",
        "Inspect handlers with source file and line number",
        "Search by signal name or receiver function",
    ]

    app_name = "dj_signals_panel"
    docs_url = "https://github.com/yassi/dj-signals-panel"
    pypi_url = "https://pypi.org/project/dj-signals-panel/"

    def get_url_name(self):
        return "index"

    def get_config(self):
        from .conf import panel_config

        return panel_config
