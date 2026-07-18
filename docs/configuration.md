# Configuration

Dj Signals Panel works out of the box with no required configuration. All options are set via a `DJ_SIGNALS_PANEL_SETTINGS` dict in your Django settings.

```python
DJ_SIGNALS_PANEL_SETTINGS = {
    'SHOW_SOURCE': False,
    'SIGNAL_MODULES': [],
    'LOAD_DEFAULT_CSS': True,
    'EXTRA_CSS': [],
}
```

## Settings Reference

### `SHOW_SOURCE`

**Type:** `bool`  
**Default:** `False`  
**Description:** Every receiver row on the signal detail page includes an expandable section for its file path/line (labelled **View Location**). When `SHOW_SOURCE` is `True`, that same section is relabelled **View Source** and additionally renders the receiver's source code with syntax highlighting.

```python
DJ_SIGNALS_PANEL_SETTINGS = {
    'SHOW_SOURCE': True,
}
```

### `SIGNAL_MODULES`

**Type:** `list[str]`  
**Default:** `[]`  
**Description:** Additional Python module paths to include in signal discovery, on top of what is found automatically. Useful when your signals are defined in modules that are not picked up by default.

```python
DJ_SIGNALS_PANEL_SETTINGS = {
    'SIGNAL_MODULES': [
        'myapp.signals',
        'otherapp.events',
    ],
}
```

### `LOAD_DEFAULT_CSS`

**Type:** `bool`  
**Default:** `True`  
**Description:** Whether to load the built-in Signals Panel stylesheet. Set to `False` to provide your own styles from scratch.

### `EXTRA_CSS`

**Type:** `list[str]`  
**Default:** `[]`  
**Description:** Additional stylesheets to load after the default CSS. Accepts static file paths or full URLs.

Static file paths are **relative to your app's `static/` subdirectory** (same convention as Django's `{% static %}` tag). A file at `myapp/static/myapp/css/overrides.css` is referenced as `myapp/css/overrides.css`.

```python
DJ_SIGNALS_PANEL_SETTINGS = {
    'EXTRA_CSS': [
        # File lives at: myapp/static/myapp/css/overrides.css
        'myapp/css/overrides.css',
        # Full URLs are also supported
        'https://cdn.example.com/theme.css',
    ],
}
```

### Theme adapters

Dj Signals Panel builds on `dj-control-room-base`, which ships optional token-override stylesheets for admin skins that don't match the classic Django admin palette. These aren't loaded automatically - add the one you need to `EXTRA_CSS`:

```python
DJ_SIGNALS_PANEL_SETTINGS = {
    'EXTRA_CSS': ['dj_control_room_base/css/themes/unfold.css'],
}
```

Currently available:

| File | For |
|---|---|
| `themes/unfold.css` | Projects using [django-unfold](https://github.com/unfoldadmin/django-unfold) as their admin skin. |

`themes/unfold.css` remaps Dj Signals Panel's accent/surface/border/muted tokens to Unfold's own CSS variables, so the panel matches the host site's configured brand color instead of the classic-admin blue.

![Signal List with django-unfold theme](https://raw.githubusercontent.com/django-control-room/dj-signals-panel/main/images/admin_signal_search_unfold.png)

See the [dj-control-room-base configuration docs](https://django-control-room.github.io/dj-control-room-base/configuration/#theme-adapters) for more on how theme adapters work and how to build your own.

## URLs Configuration

```python
# urls.py
urlpatterns = [
    path('admin/dj-signals-panel/', include('dj_signals_panel.urls')),
    path('admin/', admin.site.urls),
]
```

## Security

Dj Signals Panel uses Django's built-in admin authentication:

- Only staff users (`is_staff=True`) can access the panel
- All views require authentication via `@staff_member_required`
- No additional security configuration needed
