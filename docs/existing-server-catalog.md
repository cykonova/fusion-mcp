# Existing Fusion 360 MCP Server - Tool Catalog

> Source: `/Users/jack/Source/Fusion-360-MCP-Server`
> Stack: Python (Fusion 360 add-in), MCP over SSE/JSON-RPC
> Purpose: Reference catalog for our new focused Node/TS MCP server

## Architecture Overview

The existing server is a Fusion 360 **add-in** written in Python that registers as a remote tool (`fusion360`) with an MCP-Link server. It communicates via SSE (Server-Sent Events) and uses a thread-safe work queue to marshal API calls onto Fusion's main thread.

### Key Files

| File | Purpose |
|------|---------|
| `mcp_integration.py` (~1660 lines) | Core MCP integration, all operation handlers |
| `mcp_main.py` (~121 lines) | Add-in entry/exit, update checker |
| `lib/mcp_client.py` (~950 lines) | MCP client, SSE connection, tool registration |
| `lib/mcp_bridge.py` (~81 lines) | Bridge for Python code to call other MCP tools |
| `best_practices.md` | Fusion 360 design best practices guide |
| `config.py` | Configuration flags (DEBUG, MCP_DEBUG, MCP_AUTO_CONNECT) |

---

## Complete Operation Routing

All operations go through a single `fusion360` tool. The `operation` parameter determines routing:

```
├─ (none/default)          → Generic API call via api_path
├─ execute_python           → Run arbitrary Python code
├─ call_tool                → Call other MCP tools
├─ save_script              → Save Python script to disk
├─ load_script              → Load Python script from disk
├─ list_scripts             → List saved scripts
├─ delete_script            → Delete a script
├─ get_api_documentation    → Live API introspection
├─ get_online_documentation → Fetch Autodesk online docs
└─ get_best_practices       → Return design guidelines
```

---

## Tool Details

### 1. Generic API Call (default - no operation)

Execute any Fusion 360 API call dynamically via a dotted path.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_path` | string | yes | Dotted path to method/property |
| `args` | array | no | Positional arguments |
| `kwargs` | object | no | Keyword arguments |
| `store_as` | string | no | Store result in context for later use |
| `return_properties` | array | no | Properties to extract from result |

**Path Shortcuts:**
- `app` → `Application.get()`
- `ui` → `app.userInterface`
- `design` → `activeProduct`
- `rootComponent` → `activeProduct.rootComponent`
- `$variable_name` → Previously stored object reference
- `adsk.core.*` / `adsk.fusion.*` → Full module paths

**Special Commands:**
- `"api_path": "get_pid"` → Get Fusion process ID
- `"api_path": "clear_context"` → Clear stored objects

### 2. Python Execution (`execute_python`)

Run arbitrary Python code with full access to Fusion environment.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | string | yes | Python code to execute |
| `session_id` | string | no | Persistent session identifier |
| `persistent` | boolean | no | Retain session variables |

**Pre-injected variables:** `app`, `ui`, `design`, `rootComponent`, `mcp`, `fusion_context`

**Security concern:** No sandboxing. Full filesystem, network, and system access.

### 3. MCP Tool Bridge (`call_tool`)

Call other MCP tools from within Fusion context.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tool_name` | string | yes | MCP tool name (e.g., "sqlite", "browser") |
| `arguments` | object | yes | Arguments to pass to the tool |

**Built-in tools:** sqlite, browser, user, python, openrouter, huggingface, context7, desktop, remote, connector

### 4. Script Management

Four operations for managing Python scripts on disk:

- **`save_script`** - `filename` + `code` → saves to `user_data/python_scripts/`
- **`load_script`** - `filename` → returns code content
- **`list_scripts`** - returns array of scripts with metadata
- **`delete_script`** - `filename` → deletes script

### 5. API Documentation (3-tier system)

#### `get_api_documentation` - Live Introspection
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `search_term` | string | yes | What to search for |
| `category` | string | no | `class_name`, `member_name`, `description`, `all` |
| `max_results` | integer | no | Max results (default: 3) |

#### `get_online_documentation` - Autodesk Cloud Docs
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `class_name` | string | yes | Class name (e.g., "ExtrudeFeatures") |
| `member_name` | string | no | Method/property name |

Returns descriptions, parameter tables, code samples, and URLs.

#### `get_best_practices` - Design Guidelines
No parameters. Returns comprehensive Fusion 360 design best practices.

---

## Thread Safety Model

- **Main Thread**: All Fusion API calls execute here
- **Daemon Threads**: SSE reader, reverse call listener
- **Work Queue**: Daemon threads queue work → CustomEvent fires → main thread processes
- **Result Queue**: Per-request queue for async responses back to daemon threads

---

## What's "Too Much"

The existing server has an enormous attack surface:

1. **Arbitrary Python execution** - No sandboxing, full system access
2. **MCP tool bridging** - Can call 10+ external tools (databases, browsers, AI models)
3. **Script persistence** - Read/write arbitrary files
4. **Full API surface** - Every Fusion 360 module exposed (CAD, CAM, ECAD, simulation)
5. **No authorization** - Any connected client gets full access

### Recommendation for New Server

Focus on **Fusion 360 CAD operations only** through well-defined, typed tool calls. No arbitrary code execution, no MCP bridging, no script management. Each operation should be an explicit, documented tool - not a generic "execute anything" proxy.
