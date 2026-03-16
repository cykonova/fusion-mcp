"""3D modeling feature handlers - extrude, revolve, fillet, chamfer."""

import adsk.core
import adsk.fusion


def _get_design(app: adsk.core.Application) -> adsk.fusion.Design:
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError("No active Fusion design")
    return design


def _get_root(app: adsk.core.Application) -> adsk.fusion.Component:
    return _get_design(app).rootComponent


def _find_sketch(app: adsk.core.Application, sketch_id: str) -> adsk.fusion.Sketch:
    root = _get_root(app)
    for sk in root.sketches:
        if sk.name == sketch_id or sk.entityToken == sketch_id:
            return sk
    raise ValueError(f"Sketch not found: '{sketch_id}'")


def _operation_enum(op: str) -> int:
    op_map = {
        "new_body": adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        "join": adsk.fusion.FeatureOperations.JoinFeatureOperation,
        "cut": adsk.fusion.FeatureOperations.CutFeatureOperation,
        "intersect": adsk.fusion.FeatureOperations.IntersectFeatureOperation,
    }
    result = op_map.get(op)
    if result is None:
        raise ValueError(f"Unknown operation: '{op}'. Use new_body, join, cut, or intersect")
    return result


def extrude(app: adsk.core.Application, params: dict) -> dict:
    """Extrude a sketch profile."""
    root = _get_root(app)
    sk = _find_sketch(app, params["sketchId"])

    profile_index = params.get("profileIndex", 0)
    if profile_index >= sk.profiles.count:
        return {
            "success": False,
            "error": f"Profile index {profile_index} out of range (sketch has {sk.profiles.count} profiles)",
        }
    profile = sk.profiles.item(profile_index)

    distance = params["distance"]
    symmetric = params.get("symmetric", False)
    operation = _operation_enum(params.get("operation", "new_body"))

    extrudes = root.features.extrudeFeatures
    ext_input = extrudes.createInput(profile, operation)

    if symmetric:
        extent = adsk.fusion.SymmetricExtentDefinition.create(
            adsk.core.ValueInput.createByReal(distance / 2), True
        )
        ext_input.setSymmetricExtent(extent, True)
    else:
        extent = adsk.fusion.DistanceExtentDefinition.create(
            adsk.core.ValueInput.createByReal(distance)
        )
        ext_input.setOneSideExtent(extent, adsk.fusion.ExtentDirections.PositiveExtentDirection)

    ext = extrudes.add(ext_input)

    body_names = [b.name for b in ext.bodies]
    return {
        "success": True,
        "data": {
            "featureId": ext.entityToken,
            "featureName": ext.name,
            "bodies": body_names,
        },
    }


def revolve(app: adsk.core.Application, params: dict) -> dict:
    """Revolve a sketch profile around an axis."""
    root = _get_root(app)
    sk = _find_sketch(app, params["sketchId"])

    profile_index = params.get("profileIndex", 0)
    if profile_index >= sk.profiles.count:
        return {
            "success": False,
            "error": f"Profile index {profile_index} out of range",
        }
    profile = sk.profiles.item(profile_index)

    # Find axis - look in the sketch lines first
    axis_id = params["axisId"]
    axis = None

    # Check sketch lines
    for curve in sk.sketchCurves:
        if curve.entityToken == axis_id or (hasattr(curve, 'isConstruction') and curve.isConstruction):
            if curve.entityToken == axis_id:
                axis = curve
                break

    # Check construction axes
    if axis is None:
        for ca in root.constructionAxes:
            if ca.name == axis_id or ca.entityToken == axis_id:
                axis = ca
                break

    if axis is None:
        return {"success": False, "error": f"Axis not found: '{axis_id}'"}

    import math
    angle = params.get("angle", 360)
    operation = _operation_enum(params.get("operation", "new_body"))

    revolves = root.features.revolveFeatures
    rev_input = revolves.createInput(profile, axis, operation)

    angle_value = adsk.core.ValueInput.createByReal(math.radians(angle))
    rev_input.setAngleExtent(False, angle_value)

    rev = revolves.add(rev_input)

    body_names = [b.name for b in rev.bodies]
    return {
        "success": True,
        "data": {
            "featureId": rev.entityToken,
            "featureName": rev.name,
            "bodies": body_names,
        },
    }


def fillet(app: adsk.core.Application, params: dict) -> dict:
    """Apply fillet to edges."""
    root = _get_root(app)

    edge_ids = params["edgeIds"]
    radius = params["radius"]

    # Collect edges
    edges = adsk.core.ObjectCollection.create()
    for edge_id in edge_ids:
        found = _find_edge(root, edge_id)
        if found is None:
            return {"success": False, "error": f"Edge not found: '{edge_id}'"}
        edges.add(found)

    fillets = root.features.filletFeatures
    fillet_input = fillets.createInput()
    fillet_input.addConstantRadiusEdgeSet(
        edges, adsk.core.ValueInput.createByReal(radius), True
    )

    f = fillets.add(fillet_input)
    return {
        "success": True,
        "data": {
            "featureId": f.entityToken,
            "featureName": f.name,
        },
    }


def chamfer(app: adsk.core.Application, params: dict) -> dict:
    """Apply chamfer to edges."""
    root = _get_root(app)

    edge_ids = params["edgeIds"]
    distance = params["distance"]

    edges = adsk.core.ObjectCollection.create()
    for edge_id in edge_ids:
        found = _find_edge(root, edge_id)
        if found is None:
            return {"success": False, "error": f"Edge not found: '{edge_id}'"}
        edges.add(found)

    chamfers = root.features.chamferFeatures
    chamfer_input = chamfers.createInput2()
    chamfer_input.chamferType = adsk.fusion.ChamferTypes.EqualDistanceChamferType
    chamfer_input.addToEdgeSets(
        edges, adsk.core.ValueInput.createByReal(distance)
    )

    c = chamfers.add(chamfer_input)
    return {
        "success": True,
        "data": {
            "featureId": c.entityToken,
            "featureName": c.name,
        },
    }


def _find_edge(root: adsk.fusion.Component, edge_id: str):
    """Find an edge by entity token across all bodies."""
    for body in root.bRepBodies:
        for edge in body.edges:
            if edge.entityToken == edge_id:
                return edge
    return None
