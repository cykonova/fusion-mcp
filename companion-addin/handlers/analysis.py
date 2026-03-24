"""Analysis handlers - mass properties, interference check, section analysis."""

import adsk.core
import adsk.fusion


def _get_design(app: adsk.core.Application) -> adsk.fusion.Design:
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError("No active Fusion design")
    return design


def _get_root(app: adsk.core.Application) -> adsk.fusion.Component:
    return _get_design(app).rootComponent


def _find_body(root: adsk.fusion.Component, body_id: str):
    """Find a body by name or entity token."""
    for body in root.bRepBodies:
        if body.name == body_id or body.entityToken == body_id:
            return body
    return None


def mass_properties(app: adsk.core.Application, params: dict) -> dict:
    """Get physical/mass properties for a body or all bodies."""
    root = _get_root(app)

    body_id = params.get("bodyId")

    if body_id:
        body = _find_body(root, body_id)
        if not body:
            return {"success": False, "error": f"Body not found: '{body_id}'"}
        bodies = [body]
    else:
        bodies = [b for b in root.bRepBodies]

    if not bodies:
        return {"success": False, "error": "No bodies in the design"}

    results = []
    for body in bodies:
        props = body.physicalProperties
        com = props.centerOfMass
        bbox = body.boundingBox

        results.append({
            "name": body.name,
            "entityToken": body.entityToken,
            "area": props.area,
            "volume": props.volume,
            "mass": props.mass,
            "density": props.density,
            "centerOfMass": {
                "x": round(com.x, 6),
                "y": round(com.y, 6),
                "z": round(com.z, 6),
            },
            "boundingBox": {
                "min": {"x": bbox.minPoint.x, "y": bbox.minPoint.y, "z": bbox.minPoint.z},
                "max": {"x": bbox.maxPoint.x, "y": bbox.maxPoint.y, "z": bbox.maxPoint.z},
            },
        })

    return {
        "success": True,
        "data": {
            "bodyCount": len(results),
            "bodies": results,
        },
    }


def interference_check(app: adsk.core.Application, params: dict) -> dict:
    """Check interference between bodies."""
    root = _get_root(app)
    design = _get_design(app)

    body_ids = params["bodyIds"]
    if len(body_ids) < 2:
        return {"success": False, "error": "Need at least 2 body IDs to check interference"}

    bodies = []
    for bid in body_ids:
        body = _find_body(root, bid)
        if not body:
            return {"success": False, "error": f"Body not found: '{bid}'"}
        bodies.append(body)

    # Create interference input
    input_coll = adsk.core.ObjectCollection.create()
    for b in bodies:
        input_coll.add(b)

    interference_input = design.createInterferenceInput(input_coll)
    results = design.analyzeInterference(interference_input)

    interferences = []
    if results and results.count > 0:
        for i in range(results.count):
            result = results.item(i)
            body1 = result.entityOne
            body2 = result.entityTwo
            int_body = result.interferenceBody

            entry = {
                "body1": body1.name if body1 else "unknown",
                "body2": body2.name if body2 else "unknown",
            }
            if int_body:
                entry["interferenceVolume"] = int_body.volume

            interferences.append(entry)

    return {
        "success": True,
        "data": {
            "hasInterference": len(interferences) > 0,
            "count": len(interferences),
            "interferences": interferences,
        },
    }


def section_analysis(app: adsk.core.Application, params: dict) -> dict:
    """Create a section analysis by cutting the model with a plane.

    Creates an offset construction plane at the specified position which can be
    used for visual inspection via screenshot. Fusion 360's section analysis API
    is limited programmatically, so this provides the construction plane and
    recommends using fusion_screenshot to view the cross-section.
    """
    root = _get_root(app)

    plane_name = params.get("plane")
    plane_id = params.get("planeId")
    offset = params.get("offset", 0)

    # Resolve the base plane
    if plane_name:
        plane_map = {
            "xy": root.xYConstructionPlane,
            "xz": root.xZConstructionPlane,
            "yz": root.yZConstructionPlane,
        }
        base_plane = plane_map.get(plane_name)
        if not base_plane:
            return {"success": False, "error": f"Unknown plane: '{plane_name}'. Use xy, xz, or yz"}
    elif plane_id:
        base_plane = None
        for cp in root.constructionPlanes:
            if cp.name == plane_id or cp.entityToken == plane_id:
                base_plane = cp
                break
        if not base_plane:
            return {"success": False, "error": f"Construction plane not found: '{plane_id}'"}
    else:
        return {"success": False, "error": "Must specify either 'plane' or 'planeId'"}

    # Create an offset construction plane for the section cut
    if offset != 0:
        planes = root.constructionPlanes
        plane_input = planes.createInput()
        offset_val = adsk.core.ValueInput.createByReal(offset)
        plane_input.setByOffset(base_plane, offset_val)
        section_plane = planes.add(plane_input)
        section_plane.name = f"Section_{plane_name or 'custom'}_{offset}cm"
    else:
        section_plane = base_plane

    # Collect body cross-section info at this plane position
    bodies_info = []
    for body in root.bRepBodies:
        bbox = body.boundingBox
        bodies_info.append({
            "name": body.name,
            "volume": body.volume,
            "boundingBox": {
                "min": {"x": bbox.minPoint.x, "y": bbox.minPoint.y, "z": bbox.minPoint.z},
                "max": {"x": bbox.maxPoint.x, "y": bbox.maxPoint.y, "z": bbox.maxPoint.z},
            },
        })

    return {
        "success": True,
        "data": {
            "planeName": section_plane.name if hasattr(section_plane, 'name') else plane_name,
            "planeToken": section_plane.entityToken if hasattr(section_plane, 'entityToken') else None,
            "plane": plane_name or plane_id,
            "offset": offset,
            "bodies": bodies_info,
            "hint": "Use fusion_screenshot to capture the section view. Use fusion_set_view to orient the camera perpendicular to the section plane.",
        },
    }
