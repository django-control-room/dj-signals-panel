[![Django Control Room Panel](https://img.shields.io/badge/Django%20Control%20Room-Panel-0c4b33?logo=django)](https://github.com/yassi/dj-control-room)
[![Tests](https://github.com/yassi/dj-signals-panel/actions/workflows/test.yml/badge.svg)](https://github.com/yassi/dj-signals-panel/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/yassi/dj-signals-panel/branch/main/graph/badge.svg)](https://codecov.io/gh/yassi/dj-signals-panel)
[![PyPI version](https://badge.fury.io/py/dj-signals-panel.svg)](https://badge.fury.io/py/dj-signals-panel)
[![Python versions](https://img.shields.io/pypi/pyversions/dj-signals-panel.svg)](https://pypi.org/project/dj-signals-panel/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/dj-signals-panel.svg)](https://pypi.org/project/dj-signals-panel/)




# Django Signals Panel

See every Django signal and receiver, and where they fire. Right from the Django admin.

**Compatible with [dj-control-room](https://github.com/yassi/dj-control-room).** Register this panel in the Control Room to manage it from a centralized dashboard.

- **Official site:** [djangocontrolroom.com](https://djangocontrolroom.com)
- **Project repo:** [dj-control-room](https://github.com/yassi/dj-control-room)


## Docs

[https://yassi.github.io/dj-signals-panel/](https://yassi.github.io/dj-signals-panel/)

## Features

- **Signal discovery** - automatically discovers all registered Django signals across your project and installed apps
- **Receiver inspection** - lists every connected receiver for each signal, including function name, module, file location, sender, and dispatch UID
- **Source code viewer** - inline syntax-highlighted source for each receiver, directly in the admin
- **Search & filter** - search signals by name, module, or app; filter by app with a dropdown
- **Summary stats** - at-a-glance counts for total signals, total receivers, and signals with no receivers
- **Dark mode support** - respects Django admin's built-in dark/light mode toggle
- **No migrations required** - purely read-only introspection, zero database changes


### Project Structure

```
dj-signals-panel/
├── dj_signals_panel/         # Main package
│   ├── templates/           # Django templates
│   ├── views.py             # Django views
│   └── urls.py              # URL patterns
├── example_project/         # Example Django project
├── tests/                   # Test suite
├── images/                  # Screenshots for README
└── requirements.txt         # Development dependencies
```

## Requirements

- Python 3.9+
- Django 4.2+



## Django Control Room

Dj Signals Panel works great on its own, and it also pairs seamlessly as a panel inside [Django Control Room](https://github.com/yassi/dj-control-room) - a centralized dashboard that brings all your Django admin panels together in one place.

```bash
pip install dj-control-room dj-signals-panel
```

Visit **[djangocontrolroom.com](https://djangocontrolroom.com)** to learn more.

## Screenshots

### Django Admin Integration

Seamlessly integrated into your Django admin interface. A **DJ SIGNALS PANEL** section appears alongside your models - no migrations required.

| Light | Dark |
|-------|------|
| ![Admin Home – light](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_home.png) | ![Admin Home – dark](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_home_dark.png) |

### Signal List & Search

Browse all registered signals with summary stats (total signals, total receivers, signals with no receivers). Search by name, module, or app, and filter by app using the dropdown.

| Light | Dark |
|-------|------|
| ![Signal List – light](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_signal_search.png) | ![Signal List – dark](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_signal_search_dark.png) |

### Signal Detail

Drill into any signal to see its metadata and every connected receiver - including function name, module, file path, sender, and dispatch UID. Expand **View Source** to see syntax-highlighted source code inline.

> **Note:** The source code viewer is opt-in. Set `SHOW_SOURCE: True` in `DJ_SIGNALS_PANEL_SETTINGS` to enable it. Use `SIGNAL_MODULES` to add extra modules to signal discovery.

| Light | Dark |
|-------|------|
| ![Signal Detail – light](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_signal_detail.png) | ![Signal Detail – dark](https://raw.githubusercontent.com/yassi/dj-signals-panel/main/images/admin_signal_detail_dark.png) |


## Installation

### 1. Install the Package

```bash
pip install dj-signals-panel
```

### 2. Add to Django Settings

Add `dj_signals_panel` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dj_signals_panel',  # Add this line
    # ... your other apps
]
```

### 3. Configure Settings (Optional)

Add any custom configuration to your Django settings if needed:

```python
DJ_SIGNALS_PANEL_SETTINGS = {
    # Set True to render syntax-highlighted source code for each receiver
    'SHOW_SOURCE': False,
    # Extra modules to include in signal discovery (additive, not restrictive)
    'SIGNAL_MODULES': [],       # e.g. ['myapp.signals', 'otherapp.events']
    'LOAD_DEFAULT_CSS': True,   # Set False to skip built-in styles
    # Static paths are relative to app's static/ dir (e.g. 'myapp/css/overrides.css'
    # for a file at myapp/static/myapp/css/overrides.css). Full URLs also accepted.
    'EXTRA_CSS': [],
}
```




### 4. Include URLs

Add the Panel URLs to your main `urls.py`:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/dj-signals-panel/', include('dj_signals_panel.urls')),  # Add this line
    path('admin/', admin.site.urls),
]
```

### 5. Run Migrations and Create Superuser

```bash
python manage.py migrate
python manage.py createsuperuser  # If you don't have an admin user
```

### 6. Access the Panel

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to the Django admin at `http://127.0.0.1:8000/admin/`

3. Look for the "DJ SIGNALS PANEL" section in the admin interface



## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Development Setup

If you want to contribute to this project or set it up for local development:

### Prerequisites

- Python 3.9 or higher
- Redis server running locally
- Git
- Autoconf
- Docker

It is reccommended that you use docker since it will automate much of dev env setup

### 1. Clone the Repository

```bash
git clone https://github.com/yassi/dj-signals-panel.git
cd dj-signals-panel
```

### 2a. Set up dev environment using virtualenv

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -e . # install dj-signals-panel package locally
pip intall -r requirements.txt  # install all dev requirements

# Alternatively
make install # this will also do the above in one single command
```

### 2b. Set up dev environment using docker

```bash
make docker_up  # bring up all services (redis, memached) and dev environment container
make docker_shell  # open up a shell in the docker conatiner
```

### 3. Set Up Example Project

The repository includes an example Django project for development and testing

```bash
cd example_project
python manage.py migrate
python manage.py createsuperuser
```

### 4. Populate Test Data (Optional)

Add any custom management commands for populating test data if needed.

### 6. Run the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/admin/` to access the Django admin with Dj Signals Panel.

### 7. Running Tests

The project includes a comprehensive test suite. You can run them by using make or
by invoking pytest directly:

```bash
# build and install all dev dependencies and run all tests inside of docker container
make test_docker

# Test without the docker on your host machine.
# note that testing always requires a redis and memcached service to be up.
# these are mostly easily brought up using docker
make test_local
```
