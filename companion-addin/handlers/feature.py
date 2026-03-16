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


def _find_body(root: adsk.fusion.Component, body_id: str):
    """Find a body by name or entity token."""
    for body in root.bRepBodies:
        if body.name == body_id or body.entityToken == body_id:
            return body
    return None


def _find_face(root: adsk.fusion.Component, face_id: str):
    """Find a face by entity token across all bodies."""
    for body in root.bRepBodies:
        for face in body.faces:
            if face.entityToken == face_id:
                return face
    return None


def _find_feature(root: adsk.fusion.Component, feature_id: str):
    """Find a feature by name or entity token in the timeline."""
    design = root.parentDesign
    for i in range(design.timeline.count):
        item = design.timeline.item(i)
        entity = item.entity
        if entity and (getattr(entity, 'name', None) == feature_id or
                       getattr(entity, 'entityToken', None) == feature_id):
            return entity
    return None


def loft(app: adsk.core.Application, params: dict) -> dict:
    """Loft between two or more sketch profiles."""
    root = _get_root(app)

    sketch_ids = params["sketchIds"]
    profile_indices = params.get("profileIndices", [0] * len(sketch_ids))
    operation = _operation_enum(params.get("operation", "new_body"))
    is_solid = params.get("isSolid", True)

    if len(profile_indices) != len(sketch_ids):
        return {
            "success": False,
            "error": f"profileIndices length ({len(profile_indices)}) must match sketchIds length ({len(sketch_ids)})",
        }

    lofts = root.features.loftFeatures
    loft_input = lofts.createInput(operation)
    loft_input.isSolid = is_solid

    for i, sketch_id in enumerate(sketch_ids):
        sk = _find_sketch(app, sketch_id)
        idx = profile_indices[i]
        if idx >= sk.profiles.count:
            return {
                "success": False,
                "error": f"Profile index {idx} out of range for sketch '{sketch_id}' (has {sk.profiles.count} profiles)",
            }
        profile = sk.profiles.item(idx)
        loft_input.loftSections.add(profile)

    loft_feat = lofts.add(loft_input)
    body_names = [b.name for b in loft_feat.bodies]
    return {
        "success": True,
        "data": {
            "featureId": loft_feat.entityToken,
            "featureName": loft_feat.name,
            "bodies": body_names,
        },
    }


def sweep(app: adsk.core.Application, params: dict) -> dict:
    """Sweep a profile along a path."""
    root = _get_root(app)

    profile_sk = _find_sketch(app, params["profileSketchId"])
    profile_index = params.get("profileIndex", 0)
    if profile_index >= profile_sk.profiles.count:
        return {
            "success": False,
            "error": f"Profile index {profile_index} out of range",
        }
    profile = profile_sk.profiles.item(profile_index)

    path_sk = _find_sketch(app, params["pathSketchId"])
    path_curve_index = params.get("pathCurveIndex", 0)
    if path_curve_index >= path_sk.sketchCurves.count:
        return {
            "success": False,
            "error": f"Path curve index {path_curve_index} out of range",
        }

    # Create a path from the sketch curve
    path = root.features.createPath(path_sk.sketchCurves.item(path_curve_index))

    operation = _operation_enum(params.get("operation", "new_body"))

    sweeps = root.features.sweepFeatures
    sweep_input = sweeps.createInput(profile, path, operation)

    sweep_feat = sweeps.add(sweep_input)
    body_names = [b.name for b in sweep_feat.bodies]
    return {
        "success": True,
        "data": {
            "featureId": sweep_feat.entityToken,
            "featureName": sweep_feat.name,
            "bodies": body_names,
        },
    }


def shell(app: adsk.core.Application, params: dict) -> dict:
    """Shell (hollow out) a body."""
    root = _get_root(app)

    body = _find_body(root, params["bodyId"])
    if not body:
        return {"success": False, "error": f"Body not found: '{params['bodyId']}'"}

    thickness = params["thickness"]
    remove_face_ids = params.get("removeFaceIds", [])

    if not remove_face_ids:
        return {
            "success": False,
            "error": "Shell requires at least one face to remove (creates the opening). "
                     "Use fusion_list_bodies with includeFaces=true to find face entity tokens."
        }

    # Collect faces to remove
    faces_to_remove = adsk.core.ObjectCollection.create()
    for face_id in remove_face_ids:
        face = _find_face(root, face_id)
        if not face:
            return {"success": False, "error": f"Face not found: '{face_id}'"}
        faces_to_remove.add(face)

    shells = root.features.shellFeatures
    shell_input = shells.createInput(faces_to_remove)
    shell_input.insideThickness = adsk.core.ValueInput.createByReal(thickness)

    shell_feat = shells.add(shell_input)
    return {
        "success": True,
        "data": {
            "featureId": shell_feat.entityToken,
            "featureName": shell_feat.name,
        },
    }


def mirror(app: adsk.core.Application, params: dict) -> dict:
    """Mirror bodies or features across a plane."""
    root = _get_root(app)

    entity_ids = params["entityIds"]
    mirror_plane_name = params.get("mirrorPlane")
    mirror_plane_id = params.get("mirrorPlaneId")

    # Resolve mirror plane
    if mirror_plane_name:
        plane_map = {
            "xy": root.xYConstructionPlane,
            "xz": root.xZConstructionPlane,
            "yz": root.yZConstructionPlane,
        }
        mirror_plane = plane_map.get(mirror_plane_name)
        if not mirror_plane:
            return {"success": False, "error": f"Unknown plane: '{mirror_plane_name}'"}
    elif mirror_plane_id:
        mirror_plane = None
        for cp in root.constructionPlanes:
            if cp.name == mirror_plane_id or cp.entityToken == mirror_plane_id:
                mirror_plane = cp
                break
        if not mirror_plane:
            mirror_plane = _find_face(root, mirror_plane_id)
        if not mirror_plane:
            return {"success": False, "error": f"Mirror plane not found: '{mirror_plane_id}'"}
    else:
        return {"success": False, "error": "Must specify either mirrorPlane or mirrorPlaneId"}

    # Collect entities to mirror (try bodies first, then features)
    entities = adsk.core.ObjectCollection.create()
    for eid in entity_ids:
        entity = _find_body(root, eid)
        if not entity:
            entity = _find_feature(root, eid)
        if not entity:
            return {"success": False, "error": f"Entity not found: '{eid}'"}
        entities.add(entity)

    mirrors = root.features.mirrorFeatures
    mirror_input = mirrors.createInput(entities, mirror_plane)

    mirror_feat = mirrors.add(mirror_input)
    body_names = [b.name for b in mirror_feat.bodies]
    return {
        "success": True,
        "data": {
            "featureId": mirror_feat.entityToken,
            "featureName": mirror_feat.name,
            "bodies": body_names,
        },
    }


def pattern_rectangular(app: adsk.core.Application, params: dict) -> dict:
    """Create a rectangular pattern."""
    root = _get_root(app)

    entity_ids = params["entityIds"]
    dir1_axis = params["directionOneAxis"]
    dir1_count = params["directionOneCount"]
    dir1_spacing = params["directionOneSpacing"]
    dir2_axis = params.get("directionTwoAxis")
    dir2_count = params.get("directionTwoCount")
    dir2_spacing = params.get("directionTwoSpacing")

    # Collect entities
    entities = adsk.core.ObjectCollection.create()
    for eid in entity_ids:
        entity = _find_body(root, eid)
        if not entity:
            entity = _find_feature(root, eid)
        if not entity:
            return {"success": False, "error": f"Entity not found: '{eid}'"}
        entities.add(entity)

    # Resolve axis direction to a construction axis or linear edge
    axis_map = {
        "x": root.xConstructionAxis,
        "y": root.yConstructionAxis,
        "z": root.zConstructionAxis,
    }
    dir1 = axis_map.get(dir1_axis)
    if not dir1:
        return {"success": False, "error": f"Unknown axis: '{dir1_axis}'"}

    patterns = root.features.rectangularPatternFeatures
    pattern_input = patterns.createInput(
        entities, dir1,
        adsk.core.ValueInput.createByReal(dir1_count),
        adsk.core.ValueInput.createByReal(dir1_spacing),
        adsk.fusion.PatternDistanceType.SpacingPatternDistanceType,
    )

    if dir2_axis and dir2_count and dir2_spacing:
        dir2 = axis_map.get(dir2_axis)
        if not dir2:
            return {"success": False, "error": f"Unknown axis: '{dir2_axis}'"}
        pattern_input.setDirectionTwo(
            dir2,
            adsk.core.ValueInput.createByReal(dir2_count),
            adsk.core.ValueInput.createByReal(dir2_spacing),
        )

    pattern_feat = patterns.add(pattern_input)
    return {
        "success": True,
        "data": {
            "featureId": pattern_feat.entityToken,
            "featureName": pattern_feat.name,
        },
    }


def pattern_circular(app: adsk.core.Application, params: dict) -> dict:
    """Create a circular pattern."""
    import math

    root = _get_root(app)

    entity_ids = params["entityIds"]
    axis_id = params["axisId"]
    count = params["count"]
    total_angle = params.get("totalAngle", 360)

    # Collect entities
    entities = adsk.core.ObjectCollection.create()
    for eid in entity_ids:
        entity = _find_body(root, eid)
        if not entity:
            entity = _find_feature(root, eid)
        if not entity:
            return {"success": False, "error": f"Entity not found: '{eid}'"}
        entities.add(entity)

    # Find axis
    axis = None
    # Check construction axes by name
    axis_name_map = {"x": root.xConstructionAxis, "y": root.yConstructionAxis, "z": root.zConstructionAxis}
    axis = axis_name_map.get(axis_id)

    if not axis:
        for ca in root.constructionAxes:
            if ca.name == axis_id or ca.entityToken == axis_id:
                axis = ca
                break

    if not axis:
        for body in root.bRepBodies:
            for edge in body.edges:
                if edge.entityToken == axis_id:
                    axis = edge
                    break
            if axis:
                break

    if not axis:
        return {"success": False, "error": f"Axis not found: '{axis_id}'"}

    patterns = root.features.circularPatternFeatures
    pattern_input = patterns.createInput(entities, axis)
    pattern_input.quantity = adsk.core.ValueInput.createByReal(count)
    pattern_input.totalAngle = adsk.core.ValueInput.createByReal(math.radians(total_angle))
    pattern_input.isSymmetric = False

    pattern_feat = patterns.add(pattern_input)
    return {
        "success": True,
        "data": {
            "featureId": pattern_feat.entityToken,
            "featureName": pattern_feat.name,
        },
    }
