[![Django Control Room Panel](https://img.shields.io/badge/Django%20Control%20Room-Panel-0c4b33?logo=django)](https://github.com/django-control-room/dj-control-room)
[![Tests](https://github.com/django-control-room/dj-signals-panel/actions/workflows/test.yml/badge.svg)](https://github.com/django-control-room/dj-signals-panel/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/django-control-room/dj-signals-panel/branch/main/graph/badge.svg)](https://codecov.io/gh/django-control-room/dj-signals-panel)
[![PyPI version](https://badge.fury.io/py/dj-signals-panel.svg)](https://badge.fury.io/py/dj-signals-panel)
[![Python versions](https://img.shields.io/pypi/pyversions/dj-signals-panel.svg)](https://pypi.org/project/dj-signals-panel/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/dj-signals-panel.svg)](https://pypi.org/project/dj-signals-panel/)




# Django Signals Panel

See every Django signal and receiver, and where they fire. Right from the Django admin.

![DJ Signals Panel](https://raw.githubusercontent.com/django-control-room/dj-signals-panel/main/images/dj-signals-panel.png)


**Compatible with [dj-control-room](https://django-control-room.github.io/dj-control-room/).** Register this panel in the Control Room to manage it from a centralized dashboard.

- **Official site:** [djangocontrolroom.com](https://djangocontrolroom.com)
- **Project repo:** [dj-control-room](https://github.com/django-control-room/dj-control-room)


## Docs

[https://django-control-room.github.io/dj-signals-panel/](https://django-control-room.github.io/dj-signals-panel/)

## Features

- **Signal discovery** - automatically discovers all registered Django signals across your project and installed apps
- **Receiver inspection** - lists every connected receiver for each signal, including function name, module, file location, and sender
- **Source code viewer** - inline syntax-highlighted source for each receiver, directly in the admin
- **Search & filter** - search signals by name, module, or app; filter by app with a dropdown
- **Summary stats** - at-a-glance counts for total signals, total receivers, and signals with no receivers
- **Dark mode support** - respects Django admin's built-in dark/light mode toggle
- **django-unfold theme adapter** - opt-in stylesheet that remaps colors to match [django-unfold](https://github.com/unfoldadmin/django-unfold)'s accent/neutral palette (see [Theme adapters](https://django-control-room.github.io/dj-signals-panel/configuration/#theme-adapters))
- **AI Agent Integration (MCP)** - exposes `list_signals`, `get_receivers`, `find_signal_by_sender`, and `inspect_receiver` tools so AI agents (Cursor, Claude, etc.) can introspect your signal landscape via [dj-control-room](https://django-control-room.github.io/dj-control-room/)'s MCP server
- **No migrations required** - purely read-only introspection, zero database changes


## Requirements

- Python 3.9+
- Django 4.2+



## Django Control Room

Dj Signals Panel works great on its own, and it also pairs seamlessly as a panel inside [Django Control Room](https://django-control-room.github.io/dj-control-room/) - a centralized dashboard that brings all your Django admin panels together in one place.

```bash
pip install dj-control-room dj-signals-panel
```

Visit **[djangocontrolroom.com](https://djangocontrolroom.com)** to learn more.

## Screenshots

### Django Admin Integration

Seamlessly integrated into your Django admin interface. A **DJ SIGNALS PANEL** section appears alongside your models - no migrations required.

![Admin Home](https://raw.githubusercontent.com/django-control-room/dj-signals-panel/main/images/admin_home.png)

### Signal List & Search

Browse all registered signals with summary stats (total signals, total receivers, signals with no receivers). Search by name, module, or app, and filter by app using the dropdown.

![Signal List](https://raw.githubusercontent.com/django-control-room/dj-signals-panel/main/images/admin_signal_search.png)

### Signal Detail

Drill into any signal to see its metadata and every connected receiver - including function name, module, and sender. Expand **View Location** (or **View Source**, when `SHOW_SOURCE` is enabled) to see the file path/line and syntax-highlighted source code inline.

> **Note:** The source code viewer is opt-in. Set `SHOW_SOURCE: True` in `DJ_SIGNALS_PANEL_SETTINGS` to enable it. Use `SIGNAL_MODULES` to add extra modules to signal discovery.

![Signal Detail](https://raw.githubusercontent.com/django-control-room/dj-signals-panel/main/images/admin_signal_detail.png)

### django-unfold Theme

When running under [django-unfold](https://github.com/unfoldadmin/django-unfold), enable the bundled `unfold.css` [theme adapter](https://django-control-room.github.io/dj-signals-panel/configuration/#theme-adapters) via `EXTRA_CSS` to match the panel's colors to the host site's accent and neutral palette. This is opt-in - it is **not** applied automatically just because django-unfold is installed.

![Signal List with django-unfold theme](https://raw.githubusercontent.com/django-control-room/dj-signals-panel/main/images/admin_signal_search_unfold.png)

### django-jazzmin Theme

When running under [django-jazzmin](https://github.com/farridav/django-jazzmin), enable the bundled `jazzmin.css` [theme adapter](https://django-control-room.github.io/dj-signals-panel/configuration/#theme-adapters) via `EXTRA_CSS` to match the panel's colors to whichever Bootstrap/Bootswatch palette Jazzmin is configured with. This is opt-in - it is **not** applied automatically just because django-jazzmin is installed.

```python
DJ_SIGNALS_PANEL_SETTINGS = {
    'EXTRA_CSS': ['dj_control_room_base/css/themes/jazzmin.css'],
}
```


## Installation

```bash
pip install dj-signals-panel
```

Add it (and `dj_control_room_base`, its core dependency) to `INSTALLED_APPS`, include its URLs, and migrate:

```python
INSTALLED_APPS = [
    # ...
    'dj_control_room_base',
    'dj_signals_panel',
]
```

```python
urlpatterns = [
    path("admin/dj-control-room-base/", include("dj_control_room_base.urls")),
    path('admin/dj-signals-panel/', include('dj_signals_panel.urls')),
    path('admin/', admin.site.urls),
]
```

```bash
python manage.py migrate
```

Then visit `/admin/` and look for the "DJ SIGNALS PANEL" section.

For the full walkthrough and settings reference (source code viewer, extra signal modules, theme adapters), see the [Installation](https://django-control-room.github.io/dj-signals-panel/installation/) and [Configuration](https://django-control-room.github.io/dj-signals-panel/configuration/) docs.


## MCP Tools (AI Agent Integration)

Ships `list_signals`, `get_receivers`, `find_signal_by_sender`, and `inspect_receiver` tools that [dj-control-room](https://django-control-room.github.io/dj-control-room/)'s MCP server exposes to AI agents (Cursor, Claude, etc.), so they can look up signals, receivers, and source locations without grepping your codebase.

See [Configuration → Panel Tools (MCP)](https://django-control-room.github.io/dj-signals-panel/configuration/#panel-tools-mcp) for the full tool reference and [Scopes](https://django-control-room.github.io/dj-signals-panel/scopes/) for how agent access is permissioned separately from the admin UI.


## Contributing

Want to contribute or set up the project for local development? See [Contributing](https://django-control-room.github.io/dj-signals-panel/contributing/) for prerequisites, Docker/virtualenv setup, running the example project, and the test suite.

---

## License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/django-control-room/dj-signals-panel/blob/main/LICENSE) file for details.
