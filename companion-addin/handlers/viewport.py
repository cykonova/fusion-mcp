"""Viewport and visualization handlers."""

import adsk.core
import adsk.fusion
import base64
import tempfile
import os


def screenshot(app: adsk.core.Application, params: dict) -> dict:
    """Capture the current viewport as a base64-encoded PNG."""
    viewport = app.activeViewport

    # Save to temp file, read as base64
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.close()

    try:
        success = viewport.saveAsImageFile(tmp.name, 0, 0)  # 0,0 = use viewport size
        if not success:
            return {"success": False, "error": "Failed to capture viewport image"}

        with open(tmp.name, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")

        return {"success": True, "data": data}
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def setView(app: adsk.core.Application, params: dict) -> dict:
    """Set the viewport camera to a named view or custom eye/target."""
    viewport = app.activeViewport
    camera = viewport.camera

    named = params.get("named")
    if named:
        view_map = {
            "front": adsk.core.ViewOrientations.FrontViewOrientation,
            "back": adsk.core.ViewOrientations.BackViewOrientation,
            "left": adsk.core.ViewOrientations.LeftViewOrientation,
            "right": adsk.core.ViewOrientations.RightViewOrientation,
            "top": adsk.core.ViewOrientations.TopViewOrientation,
            "bottom": adsk.core.ViewOrientations.BottomViewOrientation,
            "iso": adsk.core.ViewOrientations.IsoTopRightViewOrientation,
        }
        orientation = view_map.get(named)
        if orientation is None:
            return {"success": False, "error": f"Unknown view: '{named}'"}

        camera.viewOrientation = orientation
        camera.isFitView = True
        viewport.camera = camera
        return {"success": True, "data": {"view": named}}

    eye = params.get("eye")
    target = params.get("target")
    if eye and target:
        camera.eye = adsk.core.Point3D.create(eye["x"], eye["y"], eye["z"])
        camera.target = adsk.core.Point3D.create(target["x"], target["y"], target["z"])
        viewport.camera = camera
        return {"success": True, "data": {"eye": eye, "target": target}}

    return {"success": False, "error": "Provide 'named' view or 'eye'+'target' positions"}


def zoomToFit(app: adsk.core.Application, params: dict) -> dict:
    """Fit all geometry or a specific entity in the viewport."""
    viewport = app.activeViewport
    camera = viewport.camera
    camera.isFitView = True
    viewport.camera = camera

    # FIXME: entityId-based zoom requires finding the entity and using
    # camera.target = entity bounding box center. Implement when we have
    # a reliable entity lookup utility.

    return {"success": True, "data": {"action": "fit_all"}}


def setVisualStyle(app: adsk.core.Application, params: dict) -> dict:
    """Set the viewport visual style."""
    viewport = app.activeViewport
    style = params.get("style")

    style_map = {
        "shaded": adsk.core.VisualStyles.ShadedVisualStyle,
        "wireframe": adsk.core.VisualStyles.WireframeVisualStyle,
        "shaded_wireframe": adsk.core.VisualStyles.ShadedWithVisibleEdgesOnlyVisualStyle,
    }
    vs = style_map.get(style)
    if vs is None:
        return {"success": False, "error": f"Unknown visual style: '{style}'"}

    viewport.visualStyle = vs
    return {"success": True, "data": {"style": style}}


def toggleVisibility(app: adsk.core.Application, params: dict) -> dict:
    """Show or hide a body, component, or construction entity by name or entity token."""
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"success": False, "error": "No active design"}

    root = design.rootComponent
    entity_id = params.get("entityId", "")
    visible = params.get("visible", True)

    entity = None

    # Search bodies
    for body in root.bRepBodies:
        if body.name == entity_id or body.entityToken == entity_id:
            entity = body
            break

    # Search occurrences (components)
    if not entity:
        for occ in root.allOccurrences:
            if occ.component.name == entity_id or occ.entityToken == entity_id:
                entity = occ
                break

    # Search construction planes
    if not entity:
        for plane in root.constructionPlanes:
            if plane.name == entity_id or plane.entityToken == entity_id:
                entity = plane
                break

    # Search construction axes
    if not entity:
        for axis in root.constructionAxes:
            if axis.name == entity_id or axis.entityToken == entity_id:
                entity = axis
                break

    # Search sketches
    if not entity:
        for sketch in root.sketches:
            if sketch.name == entity_id or sketch.entityToken == entity_id:
                entity = sketch
                break

    if not entity:
        return {"success": False, "error": f"Entity not found: '{entity_id}'"}

    # Bodies/occurrences use isVisible; construction geometry and sketches use isLightBulbOn
    try:
        entity.isVisible = visible
    except AttributeError:
        try:
            entity.isLightBulbOn = visible
        except AttributeError:
            return {"success": False, "error": f"Entity '{entity_id}' does not support visibility toggle"}
    return {
        "success": True,
        "data": {
            "entityId": entity_id,
            "visible": visible,
        },
    }


def orbit(app: adsk.core.Application, params: dict) -> dict:
    """Rotate the viewport camera by delta angles."""
    viewport = app.activeViewport
    camera = viewport.camera

    delta_yaw = params.get("deltaYaw", 0)
    delta_pitch = params.get("deltaPitch", 0)

    # Get current camera vectors
    eye = camera.eye
    target = camera.target

    import math

    # Vector from target to eye
    dx = eye.x - target.x
    dy = eye.y - target.y
    dz = eye.z - target.z

    # Convert to spherical
    r = math.sqrt(dx * dx + dy * dy + dz * dz)
    if r == 0:
        return {"success": False, "error": "Camera eye and target are coincident"}

    theta = math.atan2(dx, dz)  # yaw
    phi = math.asin(max(-1, min(1, dy / r)))  # pitch

    # Apply deltas
    theta += math.radians(delta_yaw)
    phi += math.radians(delta_pitch)

    # Clamp pitch to avoid gimbal lock
    phi = max(-math.pi / 2 + 0.01, min(math.pi / 2 - 0.01, phi))

    # Back to cartesian
    new_eye = adsk.core.Point3D.create(
        target.x + r * math.sin(theta) * math.cos(phi),
        target.y + r * math.sin(phi),
        target.z + r * math.cos(theta) * math.cos(phi),
    )

    camera.eye = new_eye
    viewport.camera = camera

    return {"success": True, "data": {"deltaYaw": delta_yaw, "deltaPitch": delta_pitch}}
