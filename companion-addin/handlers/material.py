"""Material and appearance handlers."""

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
    """Find a body by name or entity token across all components."""
    # Check root component
    for body in root.bRepBodies:
        if body.name == body_id or body.entityToken == body_id:
            return body
    # Check child occurrences
    for occ in root.allOccurrences:
        for body in occ.component.bRepBodies:
            if body.name == body_id or body.entityToken == body_id:
                return body
    return None


def set_material(app: adsk.core.Application, params: dict) -> dict:
    """Assign a material to a body by material library name."""
    root = _get_root(app)

    body_id = params["bodyId"]
    material_name = params["materialName"]

    body = _find_body(root, body_id)
    if not body:
        return {"success": False, "error": f"Body not found: '{body_id}'"}

    # Search all material libraries for the named material
    mat_libs = app.materialLibraries
    found_material = None

    for lib_idx in range(mat_libs.count):
        lib = mat_libs.item(lib_idx)
        materials = lib.materials
        for mat_idx in range(materials.count):
            mat = materials.item(mat_idx)
            if mat.name.lower() == material_name.lower():
                found_material = mat
                break
        if found_material:
            break

    if not found_material:
        # Collect some available material names to help the caller
        sample_names = []
        for lib_idx in range(mat_libs.count):
            lib = mat_libs.item(lib_idx)
            materials = lib.materials
            for mat_idx in range(min(materials.count, 10)):
                sample_names.append(materials.item(mat_idx).name)
            if len(sample_names) >= 20:
                break

        return {
            "success": False,
            "error": f"Material '{material_name}' not found. Some available materials: {sample_names}",
        }

    body.material = found_material

    # Report the updated physical properties
    props = body.physicalProperties
    return {
        "success": True,
        "data": {
            "bodyName": body.name,
            "materialName": found_material.name,
            "density": props.density,
            "mass": props.mass,
            "volume": props.volume,
        },
    }


def set_appearance(app: adsk.core.Application, params: dict) -> dict:
    """Set the visual appearance (color) of a body."""
    root = _get_root(app)
    design = _get_design(app)

    body_id = params["bodyId"]
    body = _find_body(root, body_id)
    if not body:
        return {"success": False, "error": f"Body not found: '{body_id}'"}

    appearance_name = params.get("appearanceName")
    color = params.get("color")

    if appearance_name:
        # Search appearance libraries
        mat_libs = app.materialLibraries
        found_appearance = None

        for lib_idx in range(mat_libs.count):
            lib = mat_libs.item(lib_idx)
            appearances = lib.appearances
            for app_idx in range(appearances.count):
                appear = appearances.item(app_idx)
                if appear.name.lower() == appearance_name.lower():
                    found_appearance = appear
                    break
            if found_appearance:
                break

        if not found_appearance:
            return {
                "success": False,
                "error": f"Appearance '{appearance_name}' not found in libraries",
            }

        body.appearance = found_appearance
        return {
            "success": True,
            "data": {
                "bodyName": body.name,
                "appearanceName": found_appearance.name,
            },
        }

    elif color:
        # Set color directly using RGB values
        r = color.get("r", 128)
        g = color.get("g", 128)
        b = color.get("b", 128)
        opacity = color.get("opacity", 255)

        # Get or create a custom appearance by copying from an existing one
        # Use the design's appearances collection
        custom_name = f"Custom_RGB_{r}_{g}_{b}"

        # Check if we already have this custom appearance
        existing = design.appearances.itemByName(custom_name)
        if existing:
            body.appearance = existing
        else:
            # Find a base appearance to copy (use first available)
            base_appear = None
            mat_libs = app.materialLibraries
            for lib_idx in range(mat_libs.count):
                lib = mat_libs.item(lib_idx)
                if lib.appearances.count > 0:
                    base_appear = lib.appearances.item(0)
                    break

            if not base_appear:
                return {"success": False, "error": "No base appearance found to create custom color"}

            # Copy appearance into design and modify color
            custom_appear = design.appearances.addByCopy(base_appear, custom_name)

            # Find and set the color property
            for prop_idx in range(custom_appear.appearanceProperties.count):
                prop = custom_appear.appearanceProperties.item(prop_idx)
                if hasattr(prop, 'value') and isinstance(prop.value, adsk.core.Color):
                    prop.value = adsk.core.Color.create(r, g, b, opacity)
                    break

            body.appearance = custom_appear

        return {
            "success": True,
            "data": {
                "bodyName": body.name,
                "color": {"r": r, "g": g, "b": b, "opacity": opacity},
                "appearanceName": custom_name,
            },
        }

    else:
        return {
            "success": False,
            "error": "Must specify either 'appearanceName' or 'color' ({r, g, b, opacity})",
        }
