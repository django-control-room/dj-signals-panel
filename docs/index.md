# Dj Signals Panel

Display registered Django signals and receivers, showing what fires and where.

![DJ Signals Panel](https://raw.githubusercontent.com/django-control-room/dj-signals-panel/main/images/dj-signals-panel.png)

## Overview

Dj Signals Panel is a Django admin extension that gives you full visibility into your project's signal landscape - which signals are registered, which receivers are connected, and what that receiver code actually does.

It works great standalone, and also pairs seamlessly as a panel inside [Django Control Room](https://github.com/django-control-room/dj-control-room) - a centralized dashboard that brings all your Django admin panels together in one place. Visit **[djangocontrolroom.com](https://djangocontrolroom.com)** to learn more.

## Quick Links

- [Installation](installation.md)
- [Configuration](configuration.md)
- [Development](development.md)

## Features

- **Signal discovery** - automatically discovers all registered Django signals across your project and installed apps
- **Receiver inspection** - lists every connected receiver for each signal, including function name, module, file location, and sender
- **Source code viewer** - inline syntax-highlighted source for each receiver, directly in the admin (opt-in via `SHOW_SOURCE`)
- **Additive module discovery** - use `SIGNAL_MODULES` to include signals from modules not picked up automatically
- **Search & filter** - search signals by name, module, or app; filter by app with a dropdown
- **Summary stats** - at-a-glance counts for total signals, total receivers, and signals with no receivers
- **Dark mode support** - respects Django admin's built-in dark/light mode toggle
- **django-unfold theme adapter** - opt-in stylesheet that remaps colors to match [django-unfold](https://github.com/unfoldadmin/django-unfold)'s accent/neutral palette (see [Theme adapters](configuration.md#theme-adapters))
- **django-jazzmin theme adapter** - opt-in stylesheet that remaps colors to match [django-jazzmin](https://github.com/farridav/django-jazzmin)'s Bootstrap 5 / Bootswatch palette (see [Theme adapters](configuration.md#theme-adapters))
- **No migrations required** - purely read-only introspection, zero database changes

## Screenshots

### Django Admin Integration

A **DJ SIGNALS PANEL** section appears in the Django admin alongside your models.

![Admin Home](https://raw.githubusercontent.com/django-control-room/dj-signals-panel/main/images/admin_home.png)

### Signal List & Search

Browse all registered signals with summary stats. Search by name, module, or app and filter by app using the dropdown.

![Signal List](https://raw.githubusercontent.com/django-control-room/dj-signals-panel/main/images/admin_signal_search.png)

### Signal Detail

Drill into any signal to see its metadata and every connected receiver. Expand **View Location** to see the file path/line for each receiver, or **View Source** for syntax-highlighted source code inline (requires `SHOW_SOURCE: True`).

![Signal Detail](https://raw.githubusercontent.com/django-control-room/dj-signals-panel/main/images/admin_signal_detail.png)

### django-unfold Theme

When running under [django-unfold](https://github.com/unfoldadmin/django-unfold), enable the bundled `unfold.css` [theme adapter](configuration.md#theme-adapters) via `EXTRA_CSS` to match the panel's colors to the host site's accent and neutral palette. This is opt-in - it is **not** applied automatically just because django-unfold is installed.

![Signal List with django-unfold theme](https://raw.githubusercontent.com/django-control-room/dj-signals-panel/main/images/admin_signal_search_unfold.png)


## Requirements

- Python 3.9+
- Django 4.2+

## License

MIT License - see [LICENSE](https://github.com/django-control-room/dj-signals-panel/blob/main/LICENSE) for details.
