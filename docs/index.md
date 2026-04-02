# Dj Signals Panel

Display registered Django signals and receivers, showing what fires and where.

## Overview

Dj Signals Panel is a Django admin extension that gives you full visibility into your project's signal landscape - which signals are registered, which receivers are connected, and what that receiver code actually does.

It works great standalone, and also pairs seamlessly as a panel inside [Django Control Room](https://github.com/yassi/dj-control-room) - a centralized dashboard that brings all your Django admin panels together in one place. Visit **[djangocontrolroom.com](https://djangocontrolroom.com)** to learn more.

## Quick Links

- [Installation](installation.md)
- [Configuration](configuration.md)
- [Development](development.md)

## Features

- **Signal discovery** - automatically discovers all registered Django signals across your project and installed apps
- **Receiver inspection** - lists every connected receiver for each signal, including function name, module, file location, sender, and dispatch UID
- **Source code viewer** - inline syntax-highlighted source for each receiver, directly in the admin (opt-in via `SHOW_SOURCE`)
- **Additive module discovery** - use `SIGNAL_MODULES` to include signals from modules not picked up automatically
- **Search & filter** - search signals by name, module, or app; filter by app with a dropdown
- **Summary stats** - at-a-glance counts for total signals, total receivers, and signals with no receivers
- **Dark mode support** - respects Django admin's built-in dark/light mode toggle
- **No migrations required** - purely read-only introspection, zero database changes

## Screenshots

### Django Admin Integration

A **DJ SIGNALS PANEL** section appears in the Django admin alongside your models.

| Light | Dark |
|-------|------|
| ![Admin Home – light](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_home.png) | ![Admin Home – dark](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_home_dark.png) |

### Signal List & Search

Browse all registered signals with summary stats. Search by name, module, or app and filter by app using the dropdown.

| Light | Dark |
|-------|------|
| ![Signal List – light](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_signal_search.png) | ![Signal List – dark](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_signal_search_dark.png) |

### Signal Detail

Drill into any signal to see its metadata and every connected receiver. Expand **View Source** to see syntax-highlighted source code inline (requires `SHOW_SOURCE: True`).

| Light | Dark |
|-------|------|
| ![Signal Detail – light](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_signal_detail.png) | ![Signal Detail – dark](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_signal_detail_dark.png) |

## Requirements

- Python 3.9+
- Django 4.2+

## License

MIT License - see [LICENSE](https://github.com/yassi/dj-signals-panel/blob/main/LICENSE) for details.
