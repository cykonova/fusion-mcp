"""User parameter handlers - create, update, list named parameters."""

import adsk.core
import adsk.fusion


def _get_design(app: adsk.core.Application) -> adsk.fusion.Design:
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError("No active Fusion design")
    return design


def create(app: adsk.core.Application, params: dict) -> dict:
    """Create a named user parameter."""
    design = _get_design(app)

    name = params["name"]
    value = params["value"]
    units = params.get("units", "cm")
    comment = params.get("comment", "")

    # Check if parameter already exists
    existing = design.userParameters.itemByName(name)
    if existing:
        return {
            "success": False,
            "error": f"Parameter '{name}' already exists (value={existing.value}, expression='{existing.expression}'). Use fusion_update_parameter to modify it.",
        }

    param = design.userParameters.add(
        name,
        adsk.core.ValueInput.createByString(f"{value} {units}"),
        units,
        comment,
    )

    return {
        "success": True,
        "data": {
            "name": param.name,
            "value": param.value,
            "expression": param.expression,
            "unit": param.unit,
            "comment": param.comment,
        },
    }


def update(app: adsk.core.Application, params: dict) -> dict:
    """Update an existing user parameter's value or expression."""
    design = _get_design(app)

    name = params["name"]
    param = design.userParameters.itemByName(name)
    if not param:
        # List available parameters to help the caller
        available = [p.name for p in design.userParameters]
        return {
            "success": False,
            "error": f"Parameter '{name}' not found. Available: {available}",
        }

    old_value = param.value
    old_expression = param.expression

    expression = params.get("expression")
    value = params.get("value")
    units = params.get("units")

    if expression is not None:
        param.expression = expression
    elif value is not None:
        unit_str = units if units else param.unit
        param.expression = f"{value} {unit_str}"
    else:
        return {
            "success": False,
            "error": "Must specify either 'value' or 'expression' to update.",
        }

    if params.get("comment") is not None:
        param.comment = params["comment"]

    return {
        "success": True,
        "data": {
            "name": param.name,
            "oldValue": old_value,
            "oldExpression": old_expression,
            "newValue": param.value,
            "newExpression": param.expression,
            "unit": param.unit,
        },
    }


def list_params(app: adsk.core.Application, params: dict) -> dict:
    """List user parameters, optionally including model parameters."""
    design = _get_design(app)

    include_model = params.get("includeModel", False)

    result = []

    # User parameters
    for p in design.userParameters:
        result.append({
            "name": p.name,
            "value": p.value,
            "expression": p.expression,
            "unit": p.unit,
            "comment": p.comment,
            "role": "user",
        })

    # Model parameters (auto-generated from features)
    if include_model:
        for p in design.allParameters:
            # Skip user params already added
            if p.classType() == adsk.fusion.UserParameter.classType():
                continue
            result.append({
                "name": p.name,
                "value": p.value,
                "expression": p.expression,
                "unit": p.unit,
                "comment": getattr(p, "comment", ""),
                "role": "model",
            })

    return {
        "success": True,
        "data": {
            "count": len(result),
            "parameters": result,
        },
    }
