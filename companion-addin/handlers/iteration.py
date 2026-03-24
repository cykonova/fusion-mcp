"""Design iteration handlers - undo, redo, suppress, edit feature."""

import adsk.core
import adsk.fusion


def _get_design(app: adsk.core.Application) -> adsk.fusion.Design:
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError("No active Fusion design")
    return design


def _get_root(app: adsk.core.Application) -> adsk.fusion.Component:
    return _get_design(app).rootComponent


def _find_timeline_item(design: adsk.fusion.Design, feature_id: str):
    """Find a timeline item by name or entity token."""
    tl = design.timeline
    for i in range(tl.count):
        item = tl.item(i)
        entity = item.entity
        if entity:
            if (getattr(entity, 'name', None) == feature_id or
                    getattr(entity, 'entityToken', None) == feature_id):
                return item
    return None


def undo(app: adsk.core.Application, params: dict) -> dict:
    """Undo recent operations by moving the timeline marker backward."""
    design = _get_design(app)
    tl = design.timeline
    count = params.get("count", 1)

    old_pos = tl.markerPosition
    new_pos = max(0, old_pos - count)

    if new_pos == old_pos:
        return {
            "success": True,
            "data": {
                "message": "Already at the beginning of the timeline",
                "markerPosition": old_pos,
            },
        }

    tl.markerPosition = new_pos

    return {
        "success": True,
        "data": {
            "oldMarkerPosition": old_pos,
            "newMarkerPosition": tl.markerPosition,
            "stepsUndone": old_pos - tl.markerPosition,
        },
    }


def redo(app: adsk.core.Application, params: dict) -> dict:
    """Redo operations by moving the timeline marker forward."""
    design = _get_design(app)
    tl = design.timeline
    count = params.get("count", 1)

    old_pos = tl.markerPosition
    new_pos = min(tl.count, old_pos + count)

    if new_pos == old_pos:
        return {
            "success": True,
            "data": {
                "message": "Already at the end of the timeline",
                "markerPosition": old_pos,
            },
        }

    tl.markerPosition = new_pos

    return {
        "success": True,
        "data": {
            "oldMarkerPosition": old_pos,
            "newMarkerPosition": tl.markerPosition,
            "stepsRedone": tl.markerPosition - old_pos,
        },
    }


def suppress_feature(app: adsk.core.Application, params: dict) -> dict:
    """Suppress or unsuppress a feature in the timeline."""
    design = _get_design(app)

    feature_id = params["featureId"]
    suppress = params.get("suppress", True)

    item = _find_timeline_item(design, feature_id)
    if not item:
        return {"success": False, "error": f"Feature not found in timeline: '{feature_id}'"}

    item.isSuppressed = suppress

    entity = item.entity
    return {
        "success": True,
        "data": {
            "featureName": getattr(entity, 'name', None) if entity else feature_id,
            "isSuppressed": item.isSuppressed,
        },
    }


def edit_feature(app: adsk.core.Application, params: dict) -> dict:
    """Edit parameters of an existing feature.

    Supports updating dimension values on extrude, revolve, fillet, and chamfer
    features. Uses a type-dispatch approach per feature kind.
    """
    design = _get_design(app)
    root = _get_root(app)

    feature_id = params["featureId"]
    updates = params.get("parameters", {})

    if not updates:
        return {"success": False, "error": "No parameters provided to update"}

    # Find the feature entity via timeline
    entity = None
    tl = design.timeline
    for i in range(tl.count):
        item = tl.item(i)
        e = item.entity
        if e and (getattr(e, 'name', None) == feature_id or
                  getattr(e, 'entityToken', None) == feature_id):
            entity = e
            break

    if not entity:
        return {"success": False, "error": f"Feature not found: '{feature_id}'"}

    obj_type = entity.objectType
    updated = {}

    try:
        # Strategy: find the feature's associated model parameters and update
        # their expressions directly. This avoids timeline rollback issues.

        # Extrude features
        if "ExtrudeFeature" in obj_type:
            feat = adsk.fusion.ExtrudeFeature.cast(entity)
            if "distance" in updates:
                extent = feat.extentOne
                if hasattr(extent, 'distance') and extent.distance:
                    param = extent.distance
                    param.expression = f"{updates['distance']} cm"
                    updated["distance"] = updates["distance"]
                else:
                    return {"success": False, "error": "Cannot update distance on this extrude extent type"}

        # Revolve features
        elif "RevolveFeature" in obj_type:
            feat = adsk.fusion.RevolveFeature.cast(entity)
            if "angle" in updates:
                extent = feat.extentDefinition
                if hasattr(extent, 'angle') and extent.angle:
                    param = extent.angle
                    param.expression = f"{updates['angle']} deg"
                    updated["angle"] = updates["angle"]
                else:
                    return {"success": False, "error": "Cannot update angle on this revolve extent type"}

        # Fillet features
        elif "FilletFeature" in obj_type:
            feat = adsk.fusion.FilletFeature.cast(entity)
            if "radius" in updates:
                edge_sets = feat.edgeSets
                if edge_sets.count > 0:
                    param = edge_sets.item(0).radius
                    param.expression = f"{updates['radius']} cm"
                    updated["radius"] = updates["radius"]

        # Chamfer features
        elif "ChamferFeature" in obj_type:
            feat = adsk.fusion.ChamferFeature.cast(entity)
            if "distance" in updates:
                edge_sets = feat.edgeSets
                if edge_sets.count > 0:
                    param = edge_sets.item(0).distance
                    param.expression = f"{updates['distance']} cm"
                    updated["distance"] = updates["distance"]

        else:
            return {
                "success": False,
                "error": f"Editing '{obj_type}' features is not yet supported. "
                         f"Supported: ExtrudeFeature, RevolveFeature, FilletFeature, ChamferFeature",
            }

    except Exception as e:
        return {"success": False, "error": f"Failed to update feature: {str(e)}"}

    if not updated:
        return {
            "success": False,
            "error": f"No applicable parameters found for this feature type ({obj_type}). "
                     f"Provided: {list(updates.keys())}",
        }

    return {
        "success": True,
        "data": {
            "featureName": getattr(entity, 'name', None),
            "featureType": obj_type,
            "updated": updated,
        },
    }
