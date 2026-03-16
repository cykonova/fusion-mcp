"""Document management handlers - info, new, save, export."""

import adsk.core
import adsk.fusion


def info(app: adsk.core.Application, params: dict) -> dict:
    """Get active document information."""
    doc = app.activeDocument
    if not doc:
        return {"success": False, "error": "No active document"}

    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"success": False, "error": "Active product is not a Fusion design"}

    units = design.unitsManager
    root = design.rootComponent

    return {
        "success": True,
        "data": {
            "name": doc.name,
            "isSaved": doc.isSaved,
            "units": units.defaultLengthUnits,
            "productType": app.activeProduct.productType,
            "componentCount": design.allComponents.count,
            "bodyCount": root.bRepBodies.count,
        },
    }


def new(app: adsk.core.Application, params: dict) -> dict:
    """Create a new design document."""
    doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    name = params.get("name")

    # Fusion doesn't let you rename unsaved docs directly via API,
    # but we'll return the auto-generated name
    return {
        "success": True,
        "data": {
            "name": doc.name,
            "requestedName": name,
        },
    }


def save(app: adsk.core.Application, params: dict) -> dict:
    """Save the active document."""
    doc = app.activeDocument
    if not doc:
        return {"success": False, "error": "No active document"}

    if not doc.isSaved:
        # First save requires a name/folder - can't do programmatically without more params
        return {"success": False, "error": "Document has never been saved. Save it manually first, then this tool can save subsequent changes."}

    doc.save("")
    return {"success": True, "data": {"name": doc.name}}


def export(app: adsk.core.Application, params: dict) -> dict:
    """Export the active design to a file."""
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"success": False, "error": "No active Fusion design"}

    fmt = params.get("format", "step")
    output_path = params.get("outputPath")
    if not output_path:
        return {"success": False, "error": "outputPath is required"}

    export_mgr = design.exportManager

    format_map = {
        "step": lambda: export_mgr.createSTEPExportOptions(output_path),
        "stl": lambda: export_mgr.createSTLExportOptions(design.rootComponent, output_path),
        "f3d": lambda: export_mgr.createFusionArchiveExportOptions(output_path),
        "iges": lambda: export_mgr.createIGESExportOptions(output_path),
        "sat": lambda: export_mgr.createSATExportOptions(output_path),
        "smt": lambda: export_mgr.createSMTExportOptions(output_path),
    }

    factory = format_map.get(fmt)
    if factory is None:
        return {"success": False, "error": f"Unsupported format: '{fmt}'"}

    options = factory()
    success = export_mgr.execute(options)

    if success:
        return {"success": True, "data": {"format": fmt, "path": output_path}}
    else:
        return {"success": False, "error": f"Export to {fmt} failed"}
