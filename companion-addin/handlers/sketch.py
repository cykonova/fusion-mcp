"""Sketch creation and geometry handlers."""

import adsk.core
import adsk.fusion


def _get_design(app: adsk.core.Application) -> adsk.fusion.Design:
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError("No active Fusion design")
    return design


def _get_root(app: adsk.core.Application) -> adsk.fusion.Component:
    return _get_design(app).rootComponent


def _get_plane(root: adsk.fusion.Component, plane: str) -> adsk.core.Base:
    plane_map = {
        "xy": root.xYConstructionPlane,
        "xz": root.xZConstructionPlane,
        "yz": root.yZConstructionPlane,
    }
    p = plane_map.get(plane)
    if p is None:
        raise ValueError(f"Unknown plane: '{plane}'. Use 'xy', 'xz', or 'yz'")
    return p


def _find_sketch(app: adsk.core.Application, sketch_id: str) -> adsk.fusion.Sketch:
    """Find a sketch by name or ID in the root component."""
    root = _get_root(app)
    for sk in root.sketches:
        if sk.name == sketch_id or sk.entityToken == sketch_id:
            return sk
    raise ValueError(f"Sketch not found: '{sketch_id}'")


def create(app: adsk.core.Application, params: dict) -> dict:
    """Create a new sketch on a construction plane or planar face."""
    root = _get_root(app)

    plane_name = params.get("plane")
    face_id = params.get("faceId")
    construction_plane_id = params.get("constructionPlaneId")

    if construction_plane_id:
        # Find construction plane by name or entity token
        target = None
        for cp in root.constructionPlanes:
            if cp.name == construction_plane_id or cp.entityToken == construction_plane_id:
                target = cp
                break
        if not target:
            return {"success": False, "error": f"Construction plane not found: '{construction_plane_id}'"}
        sk = root.sketches.add(target)
        return {
            "success": True,
            "data": {
                "sketchId": sk.name,
                "entityToken": sk.entityToken,
                "constructionPlane": construction_plane_id,
            },
        }

    if face_id:
        # Find planar face by entity token
        target = None
        for body in root.bRepBodies:
            for face in body.faces:
                if face.entityToken == face_id:
                    target = face
                    break
            if target:
                break
        if not target:
            return {"success": False, "error": f"Face not found: '{face_id}'"}
        sk = root.sketches.add(target)
        return {
            "success": True,
            "data": {
                "sketchId": sk.name,
                "entityToken": sk.entityToken,
                "face": face_id,
            },
        }

    # Default to standard plane
    plane_name = plane_name or "xy"
    plane = _get_plane(root, plane_name)
    sk = root.sketches.add(plane)

    return {
        "success": True,
        "data": {
            "sketchId": sk.name,
            "entityToken": sk.entityToken,
            "plane": plane_name,
        },
    }


def line(app: adsk.core.Application, params: dict) -> dict:
    """Add a line to a sketch."""
    sk = _find_sketch(app, params["sketchId"])
    lines = sk.sketchCurves.sketchLines

    p1 = adsk.core.Point3D.create(params["startX"], params["startY"], 0)
    p2 = adsk.core.Point3D.create(params["endX"], params["endY"], 0)
    ln = lines.addByTwoPoints(p1, p2)

    return {
        "success": True,
        "data": {
            "lineId": ln.entityToken,
            "start": {"x": p1.x, "y": p1.y},
            "end": {"x": p2.x, "y": p2.y},
        },
    }


def circle(app: adsk.core.Application, params: dict) -> dict:
    """Add a circle to a sketch."""
    sk = _find_sketch(app, params["sketchId"])
    circles = sk.sketchCurves.sketchCircles

    center = adsk.core.Point3D.create(params["centerX"], params["centerY"], 0)
    c = circles.addByCenterRadius(center, params["radius"])

    return {
        "success": True,
        "data": {
            "circleId": c.entityToken,
            "center": {"x": center.x, "y": center.y},
            "radius": params["radius"],
        },
    }


def rectangle(app: adsk.core.Application, params: dict) -> dict:
    """Add a rectangle to a sketch by two corner points."""
    sk = _find_sketch(app, params["sketchId"])
    lines = sk.sketchCurves.sketchLines

    p1 = adsk.core.Point3D.create(params["x1"], params["y1"], 0)
    p2 = adsk.core.Point3D.create(params["x2"], params["y2"], 0)
    lines.addTwoPointRectangle(p1, p2)

    return {
        "success": True,
        "data": {
            "corner1": {"x": params["x1"], "y": params["y1"]},
            "corner2": {"x": params["x2"], "y": params["y2"]},
        },
    }


def arc(app: adsk.core.Application, params: dict) -> dict:
    """Add an arc to a sketch."""
    sk = _find_sketch(app, params["sketchId"])
    arcs = sk.sketchCurves.sketchArcs

    mode = params["mode"]

    if mode == "three_point":
        p1 = adsk.core.Point3D.create(params["startX"], params["startY"], 0)
        p2 = adsk.core.Point3D.create(params["midOrCenterX"], params["midOrCenterY"], 0)
        p3 = adsk.core.Point3D.create(params["endXOrSweep"], params.get("endY", 0), 0)
        a = arcs.addByThreePoints(p1, p2, p3)
    elif mode == "center_point":
        import math
        center = adsk.core.Point3D.create(params["midOrCenterX"], params["midOrCenterY"], 0)
        start = adsk.core.Point3D.create(params["startX"], params["startY"], 0)
        sweep = math.radians(params["endXOrSweep"])
        a = arcs.addByCenterStartSweep(center, start, sweep)
    else:
        return {"success": False, "error": f"Unknown arc mode: '{mode}'"}

    return {
        "success": True,
        "data": {"arcId": a.entityToken},
    }


def spline(app: adsk.core.Application, params: dict) -> dict:
    """Add a spline through control points."""
    sk = _find_sketch(app, params["sketchId"])

    points = params["points"]
    point_collection = adsk.core.ObjectCollection.create()
    for pt in points:
        point_collection.add(adsk.core.Point3D.create(pt["x"], pt["y"], 0))

    sp = sk.sketchCurves.sketchFittedSplines.add(point_collection)

    return {
        "success": True,
        "data": {
            "splineId": sp.entityToken,
            "pointCount": len(points),
        },
    }


def getProfiles(app: adsk.core.Application, params: dict) -> dict:
    """List closed profiles in a sketch."""
    sk = _find_sketch(app, params["sketchId"])

    profiles = []
    for i, profile in enumerate(sk.profiles):
        bbox = profile.boundingBox
        profiles.append({
            "index": i,
            "areaProperties": {
                "minX": bbox.minPoint.x,
                "minY": bbox.minPoint.y,
                "maxX": bbox.maxPoint.x,
                "maxY": bbox.maxPoint.y,
            },
        })

    return {
        "success": True,
        "data": {
            "sketchId": sk.name,
            "profileCount": len(profiles),
            "profiles": profiles,
        },
    }


def finish(app: adsk.core.Application, params: dict) -> dict:
    """Finish/close a sketch (return to model space)."""
    # In Fusion API, sketches don't need explicit closing from the API side.
    # They're only "active" in the UI. But we can validate it exists.
    sk = _find_sketch(app, params["sketchId"])
    return {
        "success": True,
        "data": {"sketchId": sk.name, "status": "finished"},
    }


def _find_sketch_entity(sk: adsk.fusion.Sketch, entity_id: str):
    """Find a sketch entity (curve or point) by entity token."""
    for curve in sk.sketchCurves:
        if curve.entityToken == entity_id:
            return curve
    for point in sk.sketchPoints:
        if point.entityToken == entity_id:
            return point
    return None


def dimension(app: adsk.core.Application, params: dict) -> dict:
    """Add a dimensional constraint to a sketch entity."""
    sk = _find_sketch(app, params["sketchId"])
    entity_id = params["entityId"]
    value = params["value"]
    entity_id2 = params.get("entityId2")

    entity = _find_sketch_entity(sk, entity_id)
    if not entity:
        return {"success": False, "error": f"Sketch entity not found: '{entity_id}'"}

    dims = sk.sketchDimensions

    if entity_id2:
        entity2 = _find_sketch_entity(sk, entity_id2)
        if not entity2:
            return {"success": False, "error": f"Sketch entity not found: '{entity_id2}'"}
        # Distance between two entities
        mid_point = adsk.core.Point3D.create(0, 0, 0)
        dim = dims.addDistanceDimension(
            entity, entity2,
            adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
            mid_point,
        )
    else:
        # Single entity dimension - try line length, circle radius, etc.
        if hasattr(entity, 'length'):
            # Line - add length dimension
            mid = entity.geometry.evaluator.getPointAtParameter(0.5)[1] if hasattr(entity.geometry, 'evaluator') else adsk.core.Point3D.create(0, 0, 0)
            start = entity.startSketchPoint
            end = entity.endSketchPoint
            dim = dims.addDistanceDimension(
                start, end,
                adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                mid,
            )
        elif isinstance(entity, adsk.fusion.SketchCircle):
            text_point = adsk.core.Point3D.create(
                entity.centerSketchPoint.geometry.x + entity.radius + 1,
                entity.centerSketchPoint.geometry.y,
                0,
            )
            dim = dims.addRadialDimension(entity, text_point)
        else:
            return {"success": False, "error": "Cannot determine dimension type for this entity"}

    dim.parameter.value = value

    return {
        "success": True,
        "data": {
            "dimensionId": dim.entityToken,
            "value": value,
        },
    }


def constraint(app: adsk.core.Application, params: dict) -> dict:
    """Add a geometric constraint to sketch entities."""
    sk = _find_sketch(app, params["sketchId"])
    constraint_type = params["type"]
    entity_id = params["entityId"]
    entity_id2 = params.get("entityId2")

    entity = _find_sketch_entity(sk, entity_id)
    if not entity:
        return {"success": False, "error": f"Sketch entity not found: '{entity_id}'"}

    entity2 = None
    if entity_id2:
        entity2 = _find_sketch_entity(sk, entity_id2)
        if not entity2:
            return {"success": False, "error": f"Sketch entity not found: '{entity_id2}'"}

    constraints = sk.geometricConstraints

    try:
        if constraint_type == "horizontal":
            c = constraints.addHorizontal(entity)
        elif constraint_type == "vertical":
            c = constraints.addVertical(entity)
        elif constraint_type == "coincident":
            if not entity2:
                return {"success": False, "error": "coincident requires entityId2"}
            c = constraints.addCoincident(entity, entity2)
        elif constraint_type == "tangent":
            if not entity2:
                return {"success": False, "error": "tangent requires entityId2"}
            c = constraints.addTangent(entity, entity2)
        elif constraint_type == "perpendicular":
            if not entity2:
                return {"success": False, "error": "perpendicular requires entityId2"}
            c = constraints.addPerpendicular(entity, entity2)
        elif constraint_type == "parallel":
            if not entity2:
                return {"success": False, "error": "parallel requires entityId2"}
            c = constraints.addParallel(entity, entity2)
        elif constraint_type == "equal":
            if not entity2:
                return {"success": False, "error": "equal requires entityId2"}
            c = constraints.addEqual(entity, entity2)
        elif constraint_type == "concentric":
            if not entity2:
                return {"success": False, "error": "concentric requires entityId2"}
            c = constraints.addConcentric(entity, entity2)
        else:
            return {"success": False, "error": f"Unknown constraint type: '{constraint_type}'"}
    except Exception as e:
        return {"success": False, "error": f"Failed to apply {constraint_type} constraint: {e}"}

    return {
        "success": True,
        "data": {
            "constraintType": constraint_type,
        },
    }
