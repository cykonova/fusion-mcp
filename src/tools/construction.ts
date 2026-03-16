import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";

export function registerConstructionTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_construction_plane_offset", {
    description: "Create a construction plane offset from an existing plane or planar face. Use for sketching cross-sections at intervals along a limb for loft profiles.",
    inputSchema: {
      offset: z.coerce.number().describe("Offset distance (cm)"),
      fromPlane: z.enum(["xy", "xz", "yz"]).optional()
        .describe("Standard plane to offset from"),
      fromFaceId: z.string().optional()
        .describe("Planar face ID to offset from (alternative to fromPlane)"),
    },
  }, async (args) => {
    const result = await bridge.call("construction.plane_offset", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_construction_plane_at_angle", {
    description: "Create a construction plane at an angle to an existing plane, rotating around an edge or axis. Use for angled mounting surfaces and joint interfaces.",
    inputSchema: {
      angle: z.coerce.number().describe("Angle in degrees"),
      edgeId: z.string().describe("Edge or axis ID to rotate around"),
      fromPlane: z.enum(["xy", "xz", "yz"]).optional()
        .describe("Standard plane to angle from"),
      fromFaceId: z.string().optional()
        .describe("Planar face ID to angle from (alternative to fromPlane)"),
    },
  }, async (args) => {
    const result = await bridge.call("construction.plane_at_angle", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_construction_axis", {
    description: "Create a construction axis from an edge or face normal. For standard axes (x/y/z), use circular pattern's built-in axis support instead.",
    inputSchema: {
      mode: z.enum(["edge", "perpendicular_to_face"]).describe("Axis creation mode"),
      edgeId: z.string().optional().describe("Edge ID (edge mode)"),
      faceId: z.string().optional().describe("Face ID (perpendicular_to_face mode)"),
    },
  }, async (args) => {
    const result = await bridge.call("construction.axis", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_sketch_dimension", {
    description: "Add a dimensional constraint to a sketch entity (line length, circle radius, distance between entities).",
    inputSchema: {
      sketchId: z.string().describe("Sketch ID"),
      entityId: z.string().describe("Sketch entity ID to dimension"),
      value: z.coerce.number().describe("Dimension value (cm)"),
      entityId2: z.string().optional()
        .describe("Second entity ID for distance-between dimensions"),
    },
  }, async (args) => {
    const result = await bridge.call("sketch.dimension", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_sketch_constraint", {
    description: "Add a geometric constraint to sketch entities (horizontal, vertical, coincident, tangent, perpendicular, parallel, equal, concentric).",
    inputSchema: {
      sketchId: z.string().describe("Sketch ID"),
      type: z.enum(["horizontal", "vertical", "coincident", "tangent", "perpendicular", "parallel", "equal", "concentric"])
        .describe("Constraint type"),
      entityId: z.string().describe("First sketch entity ID"),
      entityId2: z.string().optional()
        .describe("Second sketch entity ID (required for tangent, perpendicular, parallel, equal, concentric)"),
    },
  }, async (args) => {
    const result = await bridge.call("sketch.constraint", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
