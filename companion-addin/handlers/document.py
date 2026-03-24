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


def list_documents(app: adsk.core.Application, params: dict) -> dict:
    """List all open documents."""
    docs = []
    for i in range(app.documents.count):
        doc = app.documents.item(i)
        is_active = doc == app.activeDocument
        docs.append({
            "name": doc.name,
            "isSaved": doc.isSaved,
            "isActive": is_active,
        })

    return {
        "success": True,
        "data": {
            "count": len(docs),
            "documents": docs,
        },
    }


def close(app: adsk.core.Application, params: dict) -> dict:
    """Close a document by name, or the active document if no name given."""
    doc_name = params.get("name")
    save_before_close = params.get("save", False)

    if doc_name:
        target = None
        for i in range(app.documents.count):
            doc = app.documents.item(i)
            if doc.name == doc_name:
                target = doc
                break
        if not target:
            available = [app.documents.item(i).name for i in range(app.documents.count)]
            return {
                "success": False,
                "error": f"Document '{doc_name}' not found. Open documents: {available}",
            }
    else:
        target = app.activeDocument
        if not target:
            return {"success": False, "error": "No active document"}

    name = target.name

    if save_before_close and target.isSaved:
        target.save("")

    target.close(save_before_close)

    return {
        "success": True,
        "data": {
            "closedDocument": name,
            "saved": save_before_close,
        },
    }


def activate(app: adsk.core.Application, params: dict) -> dict:
    """Switch to a different open document by name."""
    doc_name = params.get("name")
    if not doc_name:
        return {"success": False, "error": "name is required"}

    for i in range(app.documents.count):
        doc = app.documents.item(i)
        if doc.name == doc_name:
            doc.activate()
            return {
                "success": True,
                "data": {
                    "activatedDocument": doc.name,
                    "isSaved": doc.isSaved,
                },
            }

    available = [app.documents.item(i).name for i in range(app.documents.count)]
    return {
        "success": False,
        "error": f"Document '{doc_name}' not found. Open documents: {available}",
    }


def open(app: adsk.core.Application, params: dict) -> dict:
    """Open a Fusion 360 document from a local file path."""
    import os

    file_path = params.get("filePath")
    if not file_path:
        return {"success": False, "error": "filePath is required"}

    # Expand user home dir
    file_path = os.path.expanduser(file_path)

    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: '{file_path}'"}

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in (".f3d", ".f3z", ".step", ".stp", ".iges", ".igs", ".sat", ".smt", ".stl"):
        return {
            "success": False,
            "error": f"Unsupported file type: '{ext}'. Supported: .f3d, .f3z, .step, .stp, .iges, .igs, .sat, .smt, .stl",
        }

    import_mgr = app.importManager

    if ext in (".f3d", ".f3z"):
        options = import_mgr.createFusionArchiveImportOptions(file_path)
    elif ext in (".step", ".stp"):
        options = import_mgr.createSTEPImportOptions(file_path)
    elif ext in (".iges", ".igs"):
        options = import_mgr.createIGESImportOptions(file_path)
    elif ext in (".sat",):
        options = import_mgr.createSATImportOptions(file_path)
    elif ext in (".smt",):
        options = import_mgr.createSMTImportOptions(file_path)
    elif ext in (".stl",):
        options = import_mgr.createSTLImportOptions(file_path)
    else:
        return {"success": False, "error": f"No import handler for '{ext}'"}

    doc = import_mgr.importToNewDocument(options)
    if not doc:
        return {"success": False, "error": f"Failed to import '{file_path}'"}

    return {
        "success": True,
        "data": {
            "name": doc.name,
            "filePath": file_path,
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
