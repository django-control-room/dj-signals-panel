from dj_control_room_base.core import PanelConfig

from .tools import registry as tool_registry

panel_config = PanelConfig(
    settings_key="DJ_SIGNALS_PANEL_SETTINGS",
    defaults={
        "SIGNAL_MODULES": [],
        "SHOW_SOURCE": False,
    },
    tools=tool_registry.tools,
)
