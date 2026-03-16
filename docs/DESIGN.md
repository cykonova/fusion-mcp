# fusion-mcp - Design Document

## Overview

An MCP server that gives Claude direct tools to design humanoid Arcadian components in Autodesk Fusion 360. Built as a Node/TypeScript stdio MCP server that bridges to a thin Python companion add-in running inside Fusion 360 via HTTP on localhost.

## Purpose

The Arcadian project (Plasma) needs physical embodiment - humanoid frames, joint housings, shell panels, internal cavities for electronics. This server gives Claude the tools to experiment with 3D design directly in Fusion 360, enabling an iterative design workflow: sketch, extrude, screenshot, evaluate, adjust.

## Goals

1. **Visual feedback** - Viewport screenshots and multi-angle inspection so Claude can see what it's building
2. **Explicit tools** - Each operation is a named MCP tool with typed parameters, not a generic "execute anything" proxy
3. **Exploration-friendly** - Tools for querying, inspecting, and iterating on designs, not just blind execution
4. **Type safety** - Full TypeScript types for all tool inputs/outputs
5. **Documentation first** - Every tool is documented before implementation

## Architecture

```
┌─────────────┐         ┌──────────────────┐         ┌──────────────────────────┐
│   Claude     │──stdio──│  fusion-mcp      │──HTTP───│  Companion Add-in        │
│   (Client)   │         │  (Node/TS)       │ local   │  (Python in Fusion 360)  │
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

## Tool Phases

### Phase 1: Eyes & Hands (~25 tools)
See the scene, control the viewport, basic sketch and 3D operations.
- **Viewport**: screenshot, set view (named + custom), zoom to fit, visual styles, orbit, visibility toggle
- **Scene awareness**: document info, list components, list bodies, timeline, measure
- **Sketch**: create, line, circle, rectangle, arc, spline, get profiles, finish
- **3D**: extrude, revolve, fillet, chamfer
- **Document**: new, save, export

### Phase 2: Sculpting (~10 tools)
Organic forms needed for humanoid shapes.
- **Advanced 3D**: loft, sweep, shell, mirror, rectangular/circular patterns
- **Construction geometry**: offset planes, angled planes, axes
- **Sketch constraints**: dimensions, geometric constraints

### Phase 3: Engineering (~12 tools)
Parametric design, assembly, and analysis.
- **Parameters**: create, update, list named parameters
- **Assembly**: joints, component positioning
- **Analysis**: section cuts, interference checks, mass properties
- **Iteration**: undo, redo, suppress/unsuppress, edit features

### Phase 4: Polish (~2 tools)
Materials and appearance for mass estimation and visualization.

> Full tool specification: see `.agent/tickets/003-DefinePhase1Tools.md`

## Tech Stack

- **Runtime**: Node.js
- **Language**: TypeScript (strict mode)
- **MCP SDK**: `@modelcontextprotocol/sdk`
- **Build**: tsc
- **Package Manager**: npm
- **Companion add-in**: Python 3 (Fusion 360's embedded interpreter)

## Non-Goals

- Arbitrary Python/code execution
- MCP tool bridging (calling other MCP tools from Fusion)
- Script file management
- Browser automation
- Database integration
- AI model proxying
- CAM/manufacturing (may revisit later)
