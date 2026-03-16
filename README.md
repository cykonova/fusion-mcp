# fusion-mcp

A focused, typed MCP server for Autodesk Fusion 360 CAD operations.

## Philosophy

Unlike monolithic Fusion 360 integrations that expose arbitrary code execution and dozens of bridged tools, `fusion-mcp` provides **explicit, well-defined MCP tools** with typed parameters. Each tool does one thing.

## Tools

| Tool | Description |
|------|-------------|
| `fusion_get_document_info` | Get active document info |
| `fusion_create_sketch` | Create a sketch on a construction plane |
| `fusion_add_sketch_line` | Add a line to a sketch |
| `fusion_add_sketch_circle` | Add a circle to a sketch |
| `fusion_add_sketch_rectangle` | Add a rectangle to a sketch |
| `fusion_extrude` | Extrude a sketch profile |
| `fusion_revolve` | Revolve a sketch profile around an axis |
| `fusion_fillet` | Fillet edges of a body |
| `fusion_list_bodies` | List bodies in a component |
| `fusion_list_components` | List all components |
| `fusion_export` | Export design (STEP, STL, F3D, etc.) |

## Architecture

```
AI Client ──MCP/stdio──> fusion-mcp (Node/TS) ──HTTP──> Fusion 360 Companion Add-in
```

The MCP server runs as an external Node process. A lightweight companion add-in inside Fusion 360 receives HTTP commands and executes them on the main thread.

## Setup

```bash
npm install
npm run build
```

## Usage

```bash
# Run directly
npm start

# Or configure in your MCP client
```

## Development

```bash
npm run dev    # Watch mode
```

## Configuration

Set `FUSION_BRIDGE_URL` to override the default companion add-in address (default: `http://localhost:8765`).
