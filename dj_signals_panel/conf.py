from dj_control_room_base.core import PanelConfig

panel_config = PanelConfig(
    settings_key="DJ_SIGNALS_PANEL_SETTINGS",
    defaults={
        "SIGNAL_MODULES": [],
        "SHOW_SOURCE": False,
    },
)
