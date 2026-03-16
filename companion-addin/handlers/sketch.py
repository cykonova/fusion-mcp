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

    plane_name = params.get("plane", "xy")
    face_id = params.get("faceId")

    if face_id:
        # TODO: implement face lookup by ID
        return {"success": False, "error": "Sketching on faces not yet implemented"}

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
