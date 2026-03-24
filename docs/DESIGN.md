# fusion-mcp - Design Document

## Overview

An MCP server that gives Claude direct tools to design components in Autodesk Fusion 360. Built as a Node/TypeScript stdio MCP server that bridges to a thin Python companion add-in running inside Fusion 360 via HTTP on localhost.

## Goals

1. **Visual feedback** - Viewport screenshots and multi-angle inspection so Claude can see what it's building
2. **Explicit tools** - Each operation is a named MCP tool with typed parameters, not a generic "execute anything" proxy
3. **Exploration-friendly** - Tools for querying, inspecting, and iterating on designs, not just blind execution
4. **Type safety** - Full TypeScript types for all tool inputs/outputs
5. **Documentation first** - Every tool is documented before implementation

## Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌──────────────────────────┐
│   Claude    │──stdio──│  fusion-mcp      │──HTTP───│  Companion Add-in        │
│   (Client)  │         │  (Node/TS)       │ local   │  (Python in Fusion 360)  │
└─────────────┘         └──────────────────┘         └──────────────────────────┘
                         MCP server                    Thin HTTP server on
                         Typed tools                   daemon thread, queues
                         Bridge layer                  work to Fusion main thread
```

### Why This Split?

Fusion 360 only supports Python add-ins, and its embedded Python can't serve as a stdio MCP server (no accessible stdin/stdout, blocking would deadlock the main thread). So:

- **Node/TS MCP server** runs as a standalone process, handles MCP protocol via stdio, provides typed tool definitions
- **Python companion add-in** runs inside Fusion 360, exposes a localhost HTTP server on a daemon thread, marshals API calls to the main thread via Fusion's CustomEvent system
- **HTTP bridge** connects them - localhost only, same machine, no auth needed

### Transport

- **MCP side**: stdio (standard MCP transport for Claude Code)
- **Fusion side**: HTTP POST to `http://localhost:{port}/api` on the companion add-in
- **Request format**: `{ "method": "sketch.create", "params": { "plane": "xy" } }`
- **Response format**: `{ "success": true, "data": { ... } }` or `{ "success": false, "error": "..." }`

### Thread Safety (Companion Add-in)

Borrowed from the existing Fusion 360 MCP server's proven pattern:
1. HTTP server runs on a daemon thread
2. Incoming requests are queued to a work queue
3. CustomEvent fires to wake Fusion's main thread
4. Main thread processes the queue, executes Fusion API calls
5. Result is returned to the waiting HTTP handler via a per-request response queue

## Tools (65)

### Viewport (6)

| Tool | Description |
|------|-------------|
| `fusion_screenshot` | Capture the current viewport as a PNG image |
| `fusion_set_view` | Set camera by named view (front, top, iso, etc.) or custom eye/target |
| `fusion_zoom_to_fit` | Fit all geometry or a specific body in the viewport |
| `fusion_set_visual_style` | Switch between shaded, wireframe, and shaded+wireframe |
| `fusion_toggle_visibility` | Show/hide a body or component |
| `fusion_orbit` | Orbit the camera by horizontal/vertical angles |

### Scene (6)

| Tool | Description |
|------|-------------|
| `fusion_get_document_info` | Get active document name, units, save state |
| `fusion_create_component` | Create a new empty component, returns occurrence for assembly ops |
| `fusion_list_components` | List component hierarchy with names, IDs, and nesting |
| `fusion_list_bodies` | List bodies with volume, bounding box, optionally face details |
| `fusion_get_timeline` | Get feature timeline showing build order and suppression state |
| `fusion_measure` | Measure distance between two entities or get bounding box dimensions |

### Sketch (8)

| Tool | Description |
|------|-------------|
| `fusion_create_sketch` | Create a sketch on a plane (xy, xz, yz) or planar face |
| `fusion_sketch_line` | Draw a line between two points |
| `fusion_sketch_circle` | Draw a circle at a center point with radius |
| `fusion_sketch_rectangle` | Draw a rectangle from two corner points |
| `fusion_sketch_arc` | Draw an arc (three-point or center+start+sweep) |
| `fusion_sketch_spline` | Draw a spline through fit points |
| `fusion_get_sketch_profiles` | List closed profiles in a sketch for extrude/revolve |
| `fusion_finish_sketch` | Close the active sketch |

### Modeling (4)

| Tool | Description |
|------|-------------|
| `fusion_extrude` | Extrude a sketch profile into a 3D body |
| `fusion_revolve` | Revolve a sketch profile around an axis |
| `fusion_fillet` | Apply rounded fillet to edges |
| `fusion_chamfer` | Apply angled chamfer to edges |

### Sculpting (6)

| Tool | Description |
|------|-------------|
| `fusion_loft` | Loft between two or more profiles for organic transitions |
| `fusion_sweep` | Sweep a profile along a path curve |
| `fusion_shell` | Hollow out a solid with uniform wall thickness |
| `fusion_mirror` | Mirror bodies/features across a plane |
| `fusion_pattern_rectangular` | Rectangular array of bodies/features |
| `fusion_pattern_circular` | Circular array around an axis |

### Construction (5)

| Tool | Description |
|------|-------------|
| `fusion_construction_plane_offset` | Create a plane offset from a reference plane |
| `fusion_construction_plane_at_angle` | Create a plane at an angle to a reference |
| `fusion_construction_axis` | Create a construction axis from edge or perpendicular to face |
| `fusion_sketch_dimension` | Add a driving dimension to a sketch entity |
| `fusion_sketch_constraint` | Add geometric constraints (coincident, parallel, tangent, etc.) |

### Parameters (3)

| Tool | Description |
|------|-------------|
| `fusion_create_parameter` | Create a named user parameter for parametric design |
| `fusion_update_parameter` | Update a parameter value or expression |
| `fusion_list_parameters` | List all user/model parameters and current values |

### Analysis (3)

| Tool | Description |
|------|-------------|
| `fusion_mass_properties` | Get volume, area, mass, density, center of mass for bodies |
| `fusion_interference_check` | Check for body overlap/collision between parts |
| `fusion_section_analysis` | Create a section cut plane for cross-section inspection |

### Iteration (4)

| Tool | Description |
|------|-------------|
| `fusion_undo` | Move timeline marker backward |
| `fusion_redo` | Move timeline marker forward |
| `fusion_suppress_feature` | Temporarily disable/enable a feature without deleting |
| `fusion_edit_feature` | Edit parameters of extrude, revolve, fillet, or chamfer in place |

### Assembly (3)

| Tool | Description |
|------|-------------|
| `fusion_create_joint` | Create a joint between occurrences (rigid, revolute, slider, etc.) |
| `fusion_list_joints` | List all joints with type, motion values, and connected parts |
| `fusion_move_component` | Translate and/or rotate a component occurrence |

### Material (2)

| Tool | Description |
|------|-------------|
| `fusion_set_material` | Assign a physical material (ABS, aluminum, etc.) for mass calculations |
| `fusion_set_appearance` | Set visual appearance by library name or RGB color |

### Advanced (8)

| Tool | Description |
|------|-------------|
| `fusion_split_body` | Split a body into pieces along a plane |
| `fusion_combine_bodies` | Boolean join/cut/intersect between bodies |
| `fusion_hole` | Create simple, counterbore, or countersink holes |
| `fusion_thicken` | Convert a surface body into a solid with wall thickness |
| `fusion_offset_face` | Push/pull faces to adjust local thickness |
| `fusion_import_body` | Import geometry from STEP, STL, etc. into current design |
| `fusion_scale` | Scale a body uniformly or non-uniformly |
| `fusion_thread` | Add ISO Metric or other thread standards to cylindrical faces |

### Document (7)

| Tool | Description |
|------|-------------|
| `fusion_launch` | Launch Fusion 360 and wait for add-in readiness |
| `fusion_list_documents` | List all open documents with save state |
| `fusion_close_document` | Close a document by name or the active document |
| `fusion_open_document` | Open/import a file (.f3d, .step, .stl, etc.) |
| `fusion_new_document` | Create a new design document |
| `fusion_save` | Save the active document |
| `fusion_export` | Export to STEP, STL, F3D, IGES, SAT, SMT |

## Tech Stack

- **Runtime**: Node.js
- **Language**: TypeScript (strict mode)
- **MCP SDK**: `@modelcontextprotocol/sdk`
- **Build**: tsc
- **Package Manager**: npm
- **Companion add-in**: Python 3 (Fusion 360's embedded interpreter)

