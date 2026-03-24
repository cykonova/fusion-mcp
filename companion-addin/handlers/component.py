"""Component and body query handlers."""

import adsk.core
import adsk.fusion


def create(app: adsk.core.Application, params: dict) -> dict:
    """Create a new component and return its occurrence."""
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"success": False, "error": "No active Fusion design"}

    root = design.rootComponent
    name = params.get("name", "")

    # Create a new occurrence with a new component
    transform = adsk.core.Matrix3D.create()  # identity = at origin
    occ = root.occurrences.addNewComponent(transform)
    comp = occ.component

    if name:
        comp.name = name

    return {
        "success": True,
        "data": {
            "componentName": comp.name,
            "componentToken": comp.entityToken,
            "occurrenceName": occ.name,
            "occurrenceToken": occ.entityToken,
        },
    }


def list(app: adsk.core.Application, params: dict) -> dict:
    """List all components in the design hierarchy."""
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"success": False, "error": "No active Fusion design"}

    def _walk(comp: adsk.fusion.Component, depth: int = 0) -> dict:
        result = {
            "name": comp.name,
            "entityToken": comp.entityToken,
            "bodyCount": comp.bRepBodies.count,
            "sketchCount": comp.sketches.count,
            "depth": depth,
        }
        children = []
        for occ in comp.occurrences:
            children.append(_walk(occ.component, depth + 1))
        if children:
            result["children"] = children
        return result

    tree = _walk(design.rootComponent)
    return {"success": True, "data": tree}


def listBodies(app: adsk.core.Application, params: dict) -> dict:
    """List bodies in a component."""
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"success": False, "error": "No active Fusion design"}

    component_id = params.get("componentId")
    comp = design.rootComponent

    if component_id:
        found = None
        for c in design.allComponents:
            if c.name == component_id or c.entityToken == component_id:
                found = c
                break
        if not found:
            return {"success": False, "error": f"Component not found: '{component_id}'"}
        comp = found

    include_faces = params.get("includeFaces", False)

    bodies = []
    for body in comp.bRepBodies:
        bbox = body.boundingBox
        body_info = {
            "name": body.name,
            "entityToken": body.entityToken,
            "isVisible": body.isVisible,
            "volume": body.volume,
            "faceCount": body.faces.count,
            "boundingBox": {
                "min": {"x": bbox.minPoint.x, "y": bbox.minPoint.y, "z": bbox.minPoint.z},
                "max": {"x": bbox.maxPoint.x, "y": bbox.maxPoint.y, "z": bbox.maxPoint.z},
            },
        }
        if include_faces:
            faces = []
            for face in body.faces:
                face_info = {
                    "entityToken": face.entityToken,
                    "area": face.area,
                    "geometryType": type(face.geometry).__name__,
                }
                # Add centroid for face identification
                pt = face.centroid
                face_info["centroid"] = {"x": round(pt.x, 4), "y": round(pt.y, 4), "z": round(pt.z, 4)}
                faces.append(face_info)
            body_info["faces"] = faces
        bodies.append(body_info)

    return {
        "success": True,
        "data": {
            "component": comp.name,
            "bodyCount": len(bodies),
            "bodies": bodies,
        },
    }
