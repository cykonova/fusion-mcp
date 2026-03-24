import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";
import { zBool } from "./schema.js";

export function registerAdvancedTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_split_body", {
    description: "Split a body into two pieces along a plane. Essential for creating multi-part assemblies from a single sculpted form (e.g. split a skull into top/bottom halves).",
    inputSchema: {
      bodyId: z.string().describe("Body name or entity token to split"),
      plane: z.enum(["xy", "xz", "yz"]).optional().describe("Standard plane to split along"),
      planeId: z.string().optional().describe("Construction plane or planar face entity token"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.split_body", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_combine_bodies", {
    description: "Combine bodies with a boolean operation (join, cut, intersect). Use to merge parts, subtract cavities, or find intersections without needing an extrude.",
    inputSchema: {
      targetBodyId: z.string().describe("Target body name or entity token"),
      toolBodyIds: z.array(z.string()).min(1).describe("Tool body names or entity tokens"),
      operation: z.enum(["join", "cut", "intersect"]).default("join").describe("Boolean operation"),
      keepToolBodies: zBool().default(false).describe("Keep tool bodies after operation"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.combine_bodies", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_hole", {
    description: "Create a hole feature (simple, counterbore, or countersink). Purpose-built for fastener holes — more precise than sketch circle + extrude cut.",
    inputSchema: {
      faceId: z.string().describe("Planar face entity token to place the hole on"),
      diameter: z.coerce.number().describe("Hole diameter (cm)"),
      depth: z.coerce.number().describe("Hole depth (cm)"),
      holeType: z.enum(["simple", "counterbore", "countersink"]).default("simple").describe("Hole type"),
      positionX: z.coerce.number().default(0).describe("Hole center X offset on the face (cm)"),
      positionY: z.coerce.number().default(0).describe("Hole center Y offset on the face (cm)"),
      counterboreDiameter: z.coerce.number().optional().describe("Counterbore diameter (cm) — for counterbore type"),
      counterboreDepth: z.coerce.number().optional().describe("Counterbore depth (cm) — for counterbore type"),
      countersinkDiameter: z.coerce.number().optional().describe("Countersink diameter (cm) — for countersink type"),
      countersinkAngle: z.coerce.number().optional().describe("Countersink angle (degrees, default 90) — for countersink type"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.hole", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_thicken", {
    description: "Convert a surface body into a solid by adding uniform thickness. Critical for organic shapes created from lofted/swept surfaces.",
    inputSchema: {
      bodyId: z.string().describe("Surface body name or entity token"),
      thickness: z.coerce.number().describe("Wall thickness (cm)"),
      symmetric: zBool().default(false).describe("Thicken symmetrically (both sides of surface)"),
      operation: z.enum(["new_body", "join", "cut", "intersect"]).default("new_body").describe("Boolean operation"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.thicken", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_offset_face", {
    description: "Push/pull one or more faces by a distance. Use to locally adjust wall thickness, create recesses, or add material to specific areas.",
    inputSchema: {
      faceIds: z.array(z.string()).min(1).describe("Face entity tokens to offset"),
      distance: z.coerce.number().describe("Offset distance (cm, positive = outward, negative = inward)"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.offset_face", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_import_body", {
    description: "Import geometry from a file into the current design as reference bodies. Use to bring in existing parts (e.g. a Raspberry Pi board model) to design around.",
    inputSchema: {
      filePath: z.string().describe("Path to the file (.step, .stp, .iges, .igs, .sat, .smt, .stl, .f3d, .f3z)"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.import_body", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_scale", {
    description: "Scale a body uniformly or non-uniformly. Use uniform scaling to resize a part, or non-uniform to stretch/squash along specific axes.",
    inputSchema: {
      bodyId: z.string().describe("Body name or entity token"),
      factor: z.coerce.number().optional().describe("Uniform scale factor (e.g. 2.0 = double size)"),
      factorX: z.coerce.number().optional().describe("Non-uniform X scale factor"),
      factorY: z.coerce.number().optional().describe("Non-uniform Y scale factor"),
      factorZ: z.coerce.number().optional().describe("Non-uniform Z scale factor"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.scale", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_thread", {
    description: "Add threads to a cylindrical face. Supports ISO Metric and other thread standards. Use for threaded holes (internal) or bolts/standoffs (external).",
    inputSchema: {
      faceId: z.string().describe("Cylindrical face entity token"),
      isInternal: zBool().default(true).describe("Internal threads (hole) or external (shaft)"),
      fullLength: zBool().default(true).describe("Thread the full length of the face"),
      length: z.coerce.number().optional().describe("Thread length (cm) — only when fullLength is false"),
      threadType: z.string().optional().describe("Thread standard (e.g. 'ISO Metric profile'). Defaults to ISO Metric."),
      size: z.string().optional().describe("Thread size (e.g. '3'). Auto-detected from face if omitted."),
      designation: z.string().optional().describe("Thread designation (e.g. 'M3x0.5'). Auto-selected if omitted."),
    },
  }, async (args) => {
    const result = await bridge.call("feature.thread", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
