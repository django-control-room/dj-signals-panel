# Installation

> **Using Django Control Room?** Dj Signals Panel works as a panel inside [Django Control Room](https://github.com/django-control-room/dj-control-room). Install both and follow the Control Room setup guide at [djangocontrolroom.com](https://djangocontrolroom.com).

## 1. Install the Package

```bash
pip install dj-signals-panel

# optionally install Django control room as well
pip install dj-control-room
```

## 2. Add to Django Settings

Add `dj_signals_panel` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'dj_control_room_base', # add this core library before any panels
    'dj_signals_panel',     # Signals panel itself
    'dj_control_room',      # optional if using Django control room
    # ... your other apps
]
```

## 3. Include URLs

Add the Panel URLs to your main `urls.py`. The path must be nested **under** the admin prefix:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/dj-control-room-base/", include("dj_control_room_base.urls")),
    path('admin/dj-signals-panel/', include('dj_signals_panel.urls')),
    path("admin/dj-control-room/", include("dj_control_room.urls")),  # optional if using django control room
    path('admin/', admin.site.urls),
]
```

## 4. Access the Panel

1. Start your Django development server:
   ```bash
   python manage.py runserver
   ```

2. Navigate to `http://127.0.0.1:8000/admin/`

3. Look for the **DJ SIGNALS PANEL** section - click **Dj Signals Panel** to open it

> **Note:** Dj Signals Panel does not introduce any models or database tables. No migrations are needed.

That's it! See [Configuration](configuration.md) for optional settings like enabling the source code viewer.
