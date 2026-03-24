# Fusion MCP

A Model Context Protocol server that enables Claude to control Autodesk Fusion 360 for parametric CAD modeling. Two-layer architecture: a Node/TypeScript MCP server (stdio) communicates via HTTP bridge to a Python companion add-in running inside Fusion 360.

## Architecture

```
Claude ↔ MCP Server (Node/TS, stdio) ↔ HTTP Bridge ↔ Fusion 360 Add-in (Python)
```

- **MCP Server** (`src/`): Registers tools with zod schemas, forwards calls via `bridge.call("category.action", args)`
- **Bridge** (`src/bridge/`): HTTP client that POSTs JSON to the Fusion add-in's local server
- **Companion Add-in** (`companion-addin/`): Python HTTP server running in Fusion's process, dispatches `category.action` → `handlers.category.action(app, params)`

## Build & Run

```bash
npm install
npm run build      # tsc → dist/
```

The MCP server runs via stdio. The companion add-in must be installed in Fusion 360's AddIns directory:
```
~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/FusionMCPBridge/
```

Deploy handlers: `cp companion-addin/handlers/*.py <AddIns>/FusionMCPBridge/handlers/`

## Tools (49 across 11 modules)

| Module | Count | Category |
|--------|-------|----------|
| viewport | 6 | Screenshot, camera, zoom, orbit, visual style, visibility |
| scene | 2 | Document info, measure |
| sketch | 8 | Create, line, circle, rectangle, arc, spline, profiles, finish |
| modeling | 4 | Extrude, revolve, fillet, chamfer |
| sculpting | 6 | Loft, sweep, shell, mirror, rectangular/circular pattern |
| construction | 3 | Offset plane, angle plane, axis |
| parameters | 3 | Create, update, list user/model parameters |
| analysis | 3 | Mass properties, interference check, section analysis |
| iteration | 4 | Undo, redo, suppress feature, edit feature |
| assembly | 3 | Create joint, list joints, move component |
| document | 3 | New, save, export |

## Key Conventions

- **Response format**: All handlers return `{"success": bool, "data": {...}}` or `{"success": bool, "error": "..."}`
- **Entity lookup**: By `name` or `entityToken` (Fusion's stable ID)
- **Units**: All dimensions in cm (Fusion's internal unit)
- **`zBool()`**: Use for boolean params — MCP transport may send `"true"`/`"false"` strings
- **`z.coerce.number()`**: Use for all numeric params — values may arrive as strings

## File Organization

```
src/
  tools/          # TS tool definitions (one file per category)
  bridge/         # HTTP bridge to Fusion
companion-addin/
  handlers/       # Python handlers (one file per category)
  FusionMCPBridge.py  # Add-in entry point
.agent/
  tickets/        # Work tracking
  handoffs/       # Session continuity
```
