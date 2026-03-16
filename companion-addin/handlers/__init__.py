"""
Command handlers for the FusionMCPBridge.

Each module corresponds to a method category (e.g., "viewport", "sketch").
Each public function in a module corresponds to an action.

Method "viewport.screenshot" → handlers.viewport.screenshot(app, params)
"""

from . import viewport
from . import scene
from . import sketch
from . import feature
from . import document
from . import component
from . import timeline
from . import construction

# Expose as attributes so _dispatch can do getattr(handlers, category)
__all__ = ["viewport", "scene", "sketch", "feature", "document", "component", "timeline", "construction"]
