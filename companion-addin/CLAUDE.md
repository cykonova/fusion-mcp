# companion-addin/ — Python Fusion 360 Add-in

See root [CLAUDE.md](../CLAUDE.md) for project overview.

## Adding a New Handler Module

1. Create `handlers/<category>.py`
2. Add `from . import <category>` in `handlers/__init__.py`
3. Add to `__all__` list in `__init__.py`

Bridge dispatches `"category.action"` → `handlers.category.action(app, params)`

## Handler Function Pattern

```python
def action(app: adsk.core.Application, params: dict) -> dict:
    """Docstring."""
    design = _get_design(app)
    root = _get_root(app)
    # ... do work ...
    return {
        "success": True,
        "data": { ... },
    }
```

## Common Helpers (per module)

Most handler modules define these locally:
- `_get_design(app)` → `adsk.fusion.Design`
- `_get_root(app)` → root `Component`
- `_find_body(root, id)` — lookup by name or entityToken
- `_find_sketch(app, id)` — lookup by name or entityToken
- `_find_face(root, id)` — lookup by entityToken across all bodies
- `_find_edge(root, id)` — lookup by entityToken across all bodies
- `_operation_enum(op)` — maps string to `FeatureOperations` enum

## Deployment

Handlers must be copied to the Fusion AddIns directory after changes:
```
~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/FusionMCPBridge/handlers/
```
Then restart the add-in in Fusion (Scripts & Add-Ins dialog).
