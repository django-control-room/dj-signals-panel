# Scopes

Dj Signals Panel splits its permission checks into **scopes**: named checkpoints passed to `@panel_config.permission_required(scope)` (for views) and `scope=` (for panel tools). Every scope inherits the panel-wide `ALLOWED_GROUPS`/`REQUIRE_SUPERUSER` rule by default; a scope only behaves differently once you add an entry for it under `SCOPE_PERMISSIONS` in `DJ_SIGNALS_PANEL_SETTINGS`.

Both views and tools are enforced through the **exact same mechanism**: the same `SCOPE_PERMISSIONS` dict, the same `ALLOWED_GROUPS`/`REQUIRE_SUPERUSER` keys, the same resolution order. There is no separate permission system for AI agents. See the [Permissions and Scopes guide](https://djangocontrolroom.com/guides/control-room-permissions-and-scopes) for the full model.

## Design: separate scopes per actor type

Dj Signals Panel gives **humans (admin UI views)** and **AI agents (MCP tools)** distinct scopes, even where a tool surfaces the same underlying data as a view. This means you can grant staff full browsing access in the admin while denying (or separately restricting) automated/agent access to the same data, or vice versa, without one setting accidentally controlling both.

## Reference

| Scope | Type | Protects | Default behavior |
|---|---|---|---|
| `signal_list` | View | `index` view: browse/search the full signal list | Any staff user |
| `signal_detail` | View | `signal_detail` view: a single signal's detail page and its receivers | Any staff user |
| `agent_signal_list` | Tool | `list_signals` MCP tool | Any staff user the MCP endpoint authenticates as |
| `agent_receiver_list` | Tool | `get_receivers` MCP tool | Any staff user the MCP endpoint authenticates as |
| `agent_signal_lookup` | Tool | `find_signal_by_sender` MCP tool | Any staff user the MCP endpoint authenticates as |
| `agent_receiver_inspect` | Tool | `inspect_receiver` MCP tool (optionally includes source code via `SHOW_SOURCE`) | Any staff user the MCP endpoint authenticates as |

## Example: independent human vs. agent access

```python
DJ_SIGNALS_PANEL_SETTINGS = {
    # Panel-wide default: any staff member can browse the admin UI
    'ALLOWED_GROUPS': [],

    'SCOPE_PERMISSIONS': {
        # AI agents may list signals and receivers, but resolving a
        # receiver's source code (SHOW_SOURCE) is restricted to a
        # dedicated group, even though staff can view it freely in
        # the admin's "View Source" panel.
        'agent_receiver_inspect': {'allowed_groups': ['ai-agents-readonly']},
    },
}
```

Any scope not mentioned in `SCOPE_PERMISSIONS` simply falls back to the panel-wide rule, so you only ever need to write down the exceptions.

See [Configuration](configuration.md#panel-tools-mcp) for the rest of the panel's settings, including what each MCP tool does.
