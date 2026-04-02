# Installation

> **Using Django Control Room?** Dj Signals Panel works as a panel inside [Django Control Room](https://github.com/yassi/dj-control-room). Install both and follow the Control Room setup guide at [djangocontrolroom.com](https://djangocontrolroom.com).

## 1. Install the Package

```bash
pip install dj-signals-panel
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
    'dj_signals_panel',  # Add this
    # ... your other apps
]
```

## 3. Include URLs

Add the Panel URLs to your main `urls.py`. The path must be nested **under** the admin prefix:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/dj-signals-panel/', include('dj_signals_panel.urls')),
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
