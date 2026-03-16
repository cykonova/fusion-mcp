"""
FusionMCPBridge - Companion add-in for fusion-mcp.

Runs a lightweight HTTP server on localhost:8765 inside Fusion 360.
Receives JSON commands from the MCP server and executes them on Fusion's
main thread using the CustomEvent + work queue pattern.
"""

import adsk.core
import adsk.fusion
import threading
import queue
import json
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from functools import partial

# -- Globals --
_app: adsk.core.Application = None
_ui: adsk.core.UserInterface = None
_handlers = []  # prevent GC of event handlers

_http_server: HTTPServer = None
_http_thread: threading.Thread = None
_work_queue: queue.Queue = None
_custom_event: adsk.core.CustomEvent = None
_stop_event = threading.Event()

CUSTOM_EVENT_ID = "FusionMCPBridgeEvent"
HTTP_PORT = 8765


# =============================================================================
# HTTP Server (runs on daemon thread)
# =============================================================================

class BridgeRequestHandler(BaseHTTPRequestHandler):
    """Handles POST /api requests from the MCP server."""

    def log_message(self, format, *args):
        # Suppress default stderr logging
        pass

    def do_GET(self):
        """Health check endpoint."""
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "addin": "FusionMCPBridge"})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            request = json.loads(body)
        except Exception as e:
            self._send_json(400, {"success": False, "error": f"Bad request: {e}"})
            return

        method = request.get("method")
        params = request.get("params", {})

        if not method:
            self._send_json(400, {"success": False, "error": "Missing 'method' field"})
            return

        # Queue work for the main thread and wait for result
        result_q = queue.Queue()
        _work_queue.put({"method": method, "params": params, "result_queue": result_q})

        try:
            _app.fireCustomEvent(CUSTOM_EVENT_ID)
        except Exception:
            pass  # timer thread will also fire events

        # Block until main thread processes (timeout 30s)
        try:
            result = result_q.get(timeout=30)
            self._send_json(200, result)
        except queue.Empty:
            self._send_json(504, {"success": False, "error": "Timeout waiting for Fusion main thread"})

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


# =============================================================================
# Main Thread Event Handler (processes work queue)
# =============================================================================

class WorkQueueHandler(adsk.core.CustomEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        _process_work_queue()


def _process_work_queue():
    """Process all pending work items on Fusion's main thread."""
    max_per_batch = 10
    processed = 0

    while processed < max_per_batch:
        try:
            work_item = _work_queue.get_nowait()
        except queue.Empty:
            break

        method = work_item["method"]
        params = work_item["params"]
        result_q = work_item["result_queue"]

        try:
            result = _dispatch(method, params)
        except Exception as e:
            result = {
                "success": False,
                "error": f"{type(e).__name__}: {e}",
                "trace": traceback.format_exc(),
            }

        result_q.put(result)
        processed += 1


# =============================================================================
# Timer Thread (fires CustomEvent periodically to wake main thread)
# =============================================================================

def _timer_loop():
    """Fire custom events when work is queued or periodically for keepalive."""
    while not _stop_event.is_set():
        try:
            if not _work_queue.empty():
                _app.fireCustomEvent(CUSTOM_EVENT_ID)
        except Exception:
            pass
        _stop_event.wait(0.05)  # 50ms polling


# =============================================================================
# Command Router
# =============================================================================

def _dispatch(method: str, params: dict) -> dict:
    """Route a method string to the appropriate handler."""
    import handlers  # noqa: deferred import, on sys.path via Fusion add-in loader

    parts = method.split(".")
    if len(parts) != 2:
        return {"success": False, "error": f"Invalid method format: '{method}'. Expected 'category.action'"}

    category, action = parts

    handler_module = getattr(handlers, category, None)
    if handler_module is None:
        return {"success": False, "error": f"Unknown category: '{category}'"}

    handler_fn = getattr(handler_module, action, None)
    if handler_fn is None:
        return {"success": False, "error": f"Unknown action: '{category}.{action}'"}

    return handler_fn(_app, params)


# =============================================================================
# Add-in Lifecycle
# =============================================================================

def run(context):
    global _app, _ui, _work_queue, _custom_event, _http_server, _http_thread

    _app = adsk.core.Application.get()
    _ui = _app.userInterface
    _work_queue = queue.Queue()

    # Ensure our handlers package is importable
    import sys
    import os
    addin_dir = os.path.dirname(os.path.realpath(__file__))
    if addin_dir not in sys.path:
        sys.path.insert(0, addin_dir)

    try:
        # Register custom event for main-thread processing
        _custom_event = _app.registerCustomEvent(CUSTOM_EVENT_ID)
        handler = WorkQueueHandler()
        _custom_event.add(handler)
        _handlers.append(handler)

        # Start timer thread
        timer = threading.Thread(target=_timer_loop, daemon=True)
        timer.start()

        # Start HTTP server on daemon thread
        _http_server = HTTPServer(("127.0.0.1", HTTP_PORT), BridgeRequestHandler)
        _http_thread = threading.Thread(target=_http_server.serve_forever, daemon=True)
        _http_thread.start()

        _ui.messageBox(f"FusionMCPBridge running on http://127.0.0.1:{HTTP_PORT}")

    except Exception:
        if _ui:
            _ui.messageBox(f"FusionMCPBridge failed to start:\n{traceback.format_exc()}")


def stop(context):
    global _http_server, _custom_event

    _stop_event.set()

    if _http_server:
        _http_server.shutdown()
        _http_server = None

    if _custom_event:
        _app.unregisterCustomEvent(CUSTOM_EVENT_ID)
        _custom_event = None

    _handlers.clear()
