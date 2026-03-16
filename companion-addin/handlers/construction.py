"""Construction geometry handlers - offset planes, angled planes, axes."""

import adsk.core
import adsk.fusion
import math


def _get_design(app: adsk.core.Application) -> adsk.fusion.Design:
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError("No active Fusion design")
    return design


def _get_root(app: adsk.core.Application) -> adsk.fusion.Component:
    return _get_design(app).rootComponent


def _resolve_plane(root: adsk.fusion.Component, from_plane: str = None, from_face_id: str = None):
    """Resolve a plane reference to a construction plane or face."""
    if from_plane:
        plane_map = {
            "xy": root.xYConstructionPlane,
            "xz": root.xZConstructionPlane,
            "yz": root.yZConstructionPlane,
        }
        plane = plane_map.get(from_plane)
        if not plane:
            raise ValueError(f"Unknown plane: '{from_plane}'. Use xy, xz, or yz")
        return plane

    if from_face_id:
        for body in root.bRepBodies:
            for face in body.faces:
                if face.entityToken == from_face_id:
                    return face
        raise ValueError(f"Face not found: '{from_face_id}'")

    raise ValueError("Must specify either fromPlane or fromFaceId")


def plane_offset(app: adsk.core.Application, params: dict) -> dict:
    """Create a construction plane offset from a plane or face."""
    root = _get_root(app)

    offset = params["offset"]
    from_plane = params.get("fromPlane")
    from_face_id = params.get("fromFaceId")

    plane_entity = _resolve_plane(root, from_plane, from_face_id)

    planes = root.constructionPlanes
    plane_input = planes.createInput()
    offset_value = adsk.core.ValueInput.createByReal(offset)
    plane_input.setByOffset(plane_entity, offset_value)

    new_plane = planes.add(plane_input)
    return {
        "success": True,
        "data": {
            "planeId": new_plane.entityToken,
            "planeName": new_plane.name,
        },
    }


def plane_at_angle(app: adsk.core.Application, params: dict) -> dict:
    """Create a construction plane at an angle to a plane, rotating around an edge."""
    root = _get_root(app)

    angle = params["angle"]
    edge_id = params["edgeId"]
    from_plane = params.get("fromPlane")
    from_face_id = params.get("fromFaceId")

    plane_entity = _resolve_plane(root, from_plane, from_face_id)

    # Find the edge/axis to rotate around
    line_entity = None
    for body in root.bRepBodies:
        for edge in body.edges:
            if edge.entityToken == edge_id:
                line_entity = edge
                break
        if line_entity:
            break

    if not line_entity:
        for axis in root.constructionAxes:
            if axis.name == edge_id or axis.entityToken == edge_id:
                line_entity = axis
                break

    if not line_entity:
        return {"success": False, "error": f"Edge/axis not found: '{edge_id}'"}

    planes = root.constructionPlanes
    plane_input = planes.createInput()
    angle_value = adsk.core.ValueInput.createByString(f"{angle} deg")
    plane_input.setByAngle(line_entity, angle_value, plane_entity)

    new_plane = planes.add(plane_input)
    return {
        "success": True,
        "data": {
            "planeId": new_plane.entityToken,
            "planeName": new_plane.name,
        },
    }


def axis(app: adsk.core.Application, params: dict) -> dict:
    """Create a construction axis."""
    root = _get_root(app)
    mode = params["mode"]

    axes = root.constructionAxes
    axis_input = axes.createInput()

    if mode == "two_points":
        # FIXME: Fusion's ConstructionAxisInput API doesn't accept arbitrary Point3D
        # or InfiniteLine3D for axis creation. It requires actual geometry entities
        # (ConstructionPoints from sketch points, etc.). For standard axes, use
        # circular pattern's built-in "x"/"y"/"z" support instead.
        return {
            "success": False,
            "error": "two_points mode is not yet supported. Use 'edge' mode with a body edge, "
                     "'perpendicular_to_face' mode, or pass 'x'/'y'/'z' directly to circular pattern.",
        }
    elif mode == "edge":
        edge_id = params.get("edgeId")
        if not edge_id:
            return {"success": False, "error": "edgeId required for edge mode"}
        edge = None
        for body in root.bRepBodies:
            for e in body.edges:
                if e.entityToken == edge_id:
                    edge = e
                    break
            if edge:
                break
        if not edge:
            return {"success": False, "error": f"Edge not found: '{edge_id}'"}
        axis_input.setByEdge(edge)
    elif mode == "perpendicular_to_face":
        face_id = params.get("faceId")
        if not face_id:
            return {"success": False, "error": "faceId required for perpendicular_to_face mode"}
        face = None
        for body in root.bRepBodies:
            for f in body.faces:
                if f.entityToken == face_id:
                    face = f
                    break
            if face:
                break
        if not face:
            return {"success": False, "error": f"Face not found: '{face_id}'"}
        axis_input.setByNormalToFaceAtPoint(face, face.pointOnFace)
    else:
        return {"success": False, "error": f"Unknown axis mode: '{mode}'"}

    new_axis = axes.add(axis_input)
    return {
        "success": True,
        "data": {
            "axisId": new_axis.entityToken,
            "axisName": new_axis.name,
        },
    }
