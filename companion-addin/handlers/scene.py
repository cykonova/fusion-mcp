"""Scene awareness handlers - document info, components, bodies, timeline, measure."""

import adsk.core
import adsk.fusion


def info(app: adsk.core.Application, params: dict) -> dict:
    """Alias for document.info - get active document information."""
    doc = app.activeDocument
    if not doc:
        return {"success": False, "error": "No active document"}

    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        return {"success": False, "error": "Active product is not a Fusion design"}

    units = design.unitsManager
    return {
        "success": True,
        "data": {
            "name": doc.name,
            "isSaved": doc.isSaved,
            "units": units.defaultLengthUnits,
            "productType": app.activeProduct.productType,
        },
    }


def measure(app: adsk.core.Application, params: dict) -> dict:
    """Measure distance between entities or get mass properties."""
    # TODO: implement entity lookup and measurement
    return {"success": False, "error": "measure not yet implemented - needs entity lookup"}
