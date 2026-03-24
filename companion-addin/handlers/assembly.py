"""Assembly handlers - joints, component positioning."""

import math
import adsk.core
import adsk.fusion


def _get_design(app: adsk.core.Application) -> adsk.fusion.Design:
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError("No active Fusion design")
    return design


def _get_root(app: adsk.core.Application) -> adsk.fusion.Component:
    return _get_design(app).rootComponent


def _find_occurrence(root: adsk.fusion.Component, occ_id: str):
    """Find an occurrence by name or entity token, recursively."""
    for occ in root.allOccurrences:
        if occ.name == occ_id or occ.entityToken == occ_id:
            return occ
    return None


def _joint_type_enum(joint_type: str) -> int:
    type_map = {
        "rigid": adsk.fusion.JointTypes.RigidJointType,
        "revolute": adsk.fusion.JointTypes.RevoluteJointType,
        "slider": adsk.fusion.JointTypes.SliderJointType,
        "cylindrical": adsk.fusion.JointTypes.CylindricalJointType,
        "pin_slot": adsk.fusion.JointTypes.PinSlotJointType,
        "planar": adsk.fusion.JointTypes.PlanarJointType,
        "ball": adsk.fusion.JointTypes.BallJointType,
    }
    result = type_map.get(joint_type)
    if result is None:
        raise ValueError(f"Unknown joint type: '{joint_type}'. Use: {list(type_map.keys())}")
    return result


def create_joint(app: adsk.core.Application, params: dict) -> dict:
    """Create a joint between two component occurrences."""
    root = _get_root(app)

    occ_id1 = params["occurrenceId1"]
    occ_id2 = params["occurrenceId2"]
    joint_type_str = params.get("jointType", "rigid")

    occ1 = _find_occurrence(root, occ_id1)
    if not occ1:
        available = [o.name for o in root.allOccurrences]
        return {
            "success": False,
            "error": f"Occurrence not found: '{occ_id1}'. Available: {available}",
        }

    occ2 = _find_occurrence(root, occ_id2)
    if not occ2:
        available = [o.name for o in root.allOccurrences]
        return {
            "success": False,
            "error": f"Occurrence not found: '{occ_id2}'. Available: {available}",
        }

    # Use as-built joint — it joins occurrences at their current positions
    # without requiring specific geometry selections (faces, edges, vertices)
    as_built_joints = root.asBuiltJoints

    # Non-rigid joints require a JointGeometry for the joint origin.
    # Use the first occurrence's origin construction point.
    geometry = None
    if joint_type_str != "rigid":
        origin_point = occ1.component.originConstructionPoint
        geometry = adsk.fusion.JointGeometry.createByPoint(origin_point)

    ab_input = as_built_joints.createInput(occ1, occ2, geometry)

    # Set joint motion type on the input — each type has its own setter
    # Default is rigid (no call needed). Z-axis used as default rotation/slide axis.
    if joint_type_str == "revolute":
        ab_input.setAsRevoluteJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif joint_type_str == "slider":
        ab_input.setAsSliderJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif joint_type_str == "cylindrical":
        ab_input.setAsCylindricalJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif joint_type_str == "pin_slot":
        ab_input.setAsPinSlotJointMotion(
            adsk.fusion.JointDirections.ZAxisJointDirection,
            adsk.fusion.JointDirections.XAxisJointDirection,
        )
    elif joint_type_str == "planar":
        ab_input.setAsPlanarJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    elif joint_type_str == "ball":
        ab_input.setAsBallJointMotion()
    # "rigid" is the default, no setter needed

    joint = as_built_joints.add(ab_input)

    return {
        "success": True,
        "data": {
            "jointId": joint.entityToken,
            "jointName": joint.name,
            "jointType": joint_type_str,
            "occurrence1": occ1.name,
            "occurrence2": occ2.name,
        },
    }


def list_joints(app: adsk.core.Application, params: dict) -> dict:
    """List all joints in the design."""
    root = _get_root(app)

    type_names = {
        adsk.fusion.JointTypes.RigidJointType: "rigid",
        adsk.fusion.JointTypes.RevoluteJointType: "revolute",
        adsk.fusion.JointTypes.SliderJointType: "slider",
        adsk.fusion.JointTypes.CylindricalJointType: "cylindrical",
        adsk.fusion.JointTypes.PinSlotJointType: "pin_slot",
        adsk.fusion.JointTypes.PlanarJointType: "planar",
        adsk.fusion.JointTypes.BallJointType: "ball",
    }

    joints = []
    for j in root.joints:
        entry = {
            "jointId": j.entityToken,
            "jointName": j.name,
            "jointType": type_names.get(j.jointType, "unknown"),
            "isLocked": j.isLocked,
        }

        # Get connected occurrences
        if j.occurrenceOne:
            entry["occurrence1"] = j.occurrenceOne.name
        if j.occurrenceTwo:
            entry["occurrence2"] = j.occurrenceTwo.name

        # Get joint motion limits if available
        try:
            motion = j.jointMotion
            if hasattr(motion, 'rotationValue'):
                entry["rotationValue"] = math.degrees(motion.rotationValue)
            if hasattr(motion, 'slideValue'):
                entry["slideValue"] = motion.slideValue
            if hasattr(motion, 'rotationLimits'):
                limits = motion.rotationLimits
                if limits.isMinimumValueEnabled:
                    entry["rotationMin"] = math.degrees(limits.minimumValue)
                if limits.isMaximumValueEnabled:
                    entry["rotationMax"] = math.degrees(limits.maximumValue)
        except:
            pass

        joints.append(entry)

    # Also include as-built joints
    for j in root.asBuiltJoints:
        try:
            # AsBuiltJoint exposes joint type through jointMotion, not directly
            jt = "unknown"
            try:
                motion = j.jointMotion
                if motion:
                    jt = type_names.get(motion.jointType, "unknown")
            except:
                pass

            entry = {
                "jointId": j.entityToken,
                "jointName": j.name,
                "jointType": jt,
                "isAsBuilt": True,
            }
            if j.occurrenceOne:
                entry["occurrence1"] = j.occurrenceOne.name
            if j.occurrenceTwo:
                entry["occurrence2"] = j.occurrenceTwo.name
            joints.append(entry)
        except RuntimeError:
            # Skip joints with invalid state (e.g. undone/suppressed)
            pass

    return {
        "success": True,
        "data": {
            "count": len(joints),
            "joints": joints,
        },
    }


def move_component(app: adsk.core.Application, params: dict) -> dict:
    """Move a component occurrence via translation and/or rotation."""
    root = _get_root(app)

    occ_id = params["occurrenceId"]
    occ = _find_occurrence(root, occ_id)
    if not occ:
        available = [o.name for o in root.allOccurrences]
        return {
            "success": False,
            "error": f"Occurrence not found: '{occ_id}'. Available: {available}",
        }

    transform = occ.transform

    # Apply translation
    translation = params.get("translation")
    if translation:
        x = translation.get("x", 0)
        y = translation.get("y", 0)
        z = translation.get("z", 0)
        translation_vec = adsk.core.Vector3D.create(x, y, z)
        transform.translation = adsk.core.Vector3D.create(
            transform.translation.x + x,
            transform.translation.y + y,
            transform.translation.z + z,
        )

    # Apply rotation
    rotation = params.get("rotation")
    if rotation:
        axis_name = rotation.get("axis", "z")
        angle = rotation.get("angle", 0)

        axis_map = {
            "x": adsk.core.Vector3D.create(1, 0, 0),
            "y": adsk.core.Vector3D.create(0, 1, 0),
            "z": adsk.core.Vector3D.create(0, 0, 1),
        }
        axis_vec = axis_map.get(axis_name)
        if not axis_vec:
            return {"success": False, "error": f"Unknown axis: '{axis_name}'. Use x, y, or z"}

        origin = adsk.core.Point3D.create(0, 0, 0)
        rot_matrix = adsk.core.Matrix3D.create()
        rot_matrix.setToRotation(math.radians(angle), axis_vec, origin)

        transform.transformBy(rot_matrix)

    occ.transform = transform

    # Report new position
    new_trans = occ.transform.translation
    return {
        "success": True,
        "data": {
            "occurrenceName": occ.name,
            "position": {
                "x": round(new_trans.x, 6),
                "y": round(new_trans.y, 6),
                "z": round(new_trans.z, 6),
            },
        },
    }
