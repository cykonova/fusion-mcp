"""Scene awareness handlers - document info, components, bodies, timeline, measure."""

import adsk.core
import adsk.fusion


def info(app: adsk.core.Application, params: dict) -> dict:
    """Alias for document.info - get active document information."""
    doc = app.activeDocument
    if not doc:
        return {"success": False, "error": "No active document"}

    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"success": False, "error": "Active product is not a Fusion design"}

    units = design.unitsManager
    return {
        "success": True,
        "data": {
            "name": doc.name,
            "isSaved": doc.isSaved,
            "units": units.defaultLengthUnits,
            "productType": app.activeProduct.productType,
        },
    }


def measure(app: adsk.core.Application, params: dict) -> dict:
    """Measure minimum distance between two entities (bodies, faces, edges)."""
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"success": False, "error": "No active Fusion design"}

    root = design.rootComponent
    entity_id1 = params.get("entityId1")
    entity_id2 = params.get("entityId2")

    if not entity_id1:
        return {"success": False, "error": "entityId1 is required"}

    entity1 = _find_entity(root, entity_id1)
    if not entity1:
        return {"success": False, "error": f"Entity not found: '{entity_id1}'"}

    if not entity_id2:
        # Single entity — return bounding box dimensions
        if hasattr(entity1, 'boundingBox'):
            bbox = entity1.boundingBox
            dx = bbox.maxPoint.x - bbox.minPoint.x
            dy = bbox.maxPoint.y - bbox.minPoint.y
            dz = bbox.maxPoint.z - bbox.minPoint.z
            return {
                "success": True,
                "data": {
                    "type": "bounding_box",
                    "sizeX": round(dx, 6),
                    "sizeY": round(dy, 6),
                    "sizeZ": round(dz, 6),
                },
            }
        return {"success": False, "error": "Entity does not have a bounding box"}

    entity2 = _find_entity(root, entity_id2)
    if not entity2:
        return {"success": False, "error": f"Entity not found: '{entity_id2}'"}

    # Use MeasureManager for distance between entities
    measure_mgr = app.measureManager
    try:
        result = measure_mgr.measureMinimumDistance(entity1, entity2)
        return {
            "success": True,
            "data": {
                "type": "minimum_distance",
                "distance": round(result.value, 6),
                "point1": {
                    "x": round(result.positionOne.x, 6),
                    "y": round(result.positionOne.y, 6),
                    "z": round(result.positionOne.z, 6),
                },
                "point2": {
                    "x": round(result.positionTwo.x, 6),
                    "y": round(result.positionTwo.y, 6),
                    "z": round(result.positionTwo.z, 6),
                },
            },
        }
    except Exception as e:
        return {"success": False, "error": f"Measurement failed: {str(e)}"}


def _find_entity(root: adsk.fusion.Component, entity_id: str):
    """Find a body, face, or edge by name or entity token."""
    # Check bodies by name or token
    for body in root.bRepBodies:
        if body.name == entity_id or body.entityToken == entity_id:
            return body
        # Check faces
        for face in body.faces:
            if face.entityToken == entity_id:
                return face
        # Check edges
        for edge in body.edges:
            if edge.entityToken == entity_id:
                return edge

    # Check child occurrences
    for occ in root.allOccurrences:
        for body in occ.component.bRepBodies:
            if body.name == entity_id or body.entityToken == entity_id:
                return body
            for face in body.faces:
                if face.entityToken == entity_id:
                    return face
            for edge in body.edges:
                if edge.entityToken == entity_id:
                    return edge

    return None
