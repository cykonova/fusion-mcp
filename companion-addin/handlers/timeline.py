"""Timeline query handler."""

import adsk.core
import adsk.fusion


def get(app: adsk.core.Application, params: dict) -> dict:
    """Get the design timeline."""
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"success": False, "error": "No active Fusion design"}

    tl = design.timeline
    items = []
    for i in range(tl.count):
        item = tl.item(i)
        entry = {
            "index": i,
            "name": item.name if hasattr(item, 'name') else f"Item {i}",
            "isSuppressed": item.isSuppressed,
            "isGroup": item.isGroup,
        }
        # Try to get the entity type
        entity = item.entity
        if entity:
            entry["entityType"] = entity.objectType
        items.append(entry)

    return {
        "success": True,
        "data": {
            "count": tl.count,
            "markerPosition": tl.markerPosition,
            "items": items,
        },
    }
