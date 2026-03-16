# fusion-mcp - Design Document

## Overview

A focused, typed Node/TypeScript MCP server for Autodesk Fusion 360. Unlike the existing Python-based server that exposes arbitrary code execution and 10+ external tool bridges, this server provides **explicit, well-defined tools** for Fusion 360 CAD operations.

## Goals

1. **Explicit tools** - Each operation is a named MCP tool with typed parameters
2. **Least privilege** - Only expose what's needed for CAD workflows
3. **Type safety** - Full TypeScript types for all tool inputs/outputs
4. **Documentation first** - Every tool is documented before implementation
5. **Composable** - Tools are small and composable, not monolithic

## Architecture

```
┌─────────────┐       ┌──────────────┐       ┌─────────────────┐
│  AI Client   │──MCP──│  fusion-mcp  │──HTTP──│  Fusion 360 API │
│  (Claude)    │       │  (Node/TS)   │       │  (Add-in/REST)  │
└─────────────┘       └──────────────┘       └─────────────────┘
```

### Communication with Fusion 360

The existing server runs as a Fusion 360 add-in (Python inside Fusion's process). Our server runs as an **external Node process** and communicates with a lightweight Fusion 360 add-in companion via HTTP/WebSocket.

This separation provides:
- Independent lifecycle (server doesn't crash with Fusion)
- Type safety in the MCP layer
- Easier testing (mock the Fusion bridge)
- Clear security boundary

### Transport

- **MCP side**: stdio (standard MCP transport)
- **Fusion side**: HTTP to a lightweight companion add-in running inside Fusion 360

## Tool Categories (Planned)

### Phase 1 - Core CAD
- Document management (new, open, save, export)
- Sketch operations (create, add geometry, constrain, close)
- 3D operations (extrude, revolve, fillet, chamfer)
- Component/body management

### Phase 2 - Design Intelligence
- API documentation lookup
- Best practices guidance
- Design validation

### Phase 3 - Advanced
- Timeline manipulation
- Joint/assembly operations
- Parameter management
- CAM basics (if needed)

## Tech Stack

- **Runtime**: Node.js
- **Language**: TypeScript (strict mode)
- **MCP SDK**: `@modelcontextprotocol/sdk`
- **Build**: tsc
- **Package Manager**: npm

## Non-Goals

- Arbitrary Python/code execution
- MCP tool bridging (calling other MCP tools)
- Script file management
- Browser automation
- Database integration
- AI model proxying
