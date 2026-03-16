import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";

export function registerConstructionTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_construction_plane_offset", {
    description: "Create a construction plane offset from an existing plane or planar face. Use for sketching cross-sections at intervals along a limb for loft profiles.",
    inputSchema: {
      offset: z.number().describe("Offset distance (cm)"),
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
      angle: z.number().describe("Angle in degrees"),
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
    description: "Create a construction axis. Use for revolve operations, circular pattern centers, and reference geometry.",
    inputSchema: {
      mode: z.enum(["two_points", "edge", "perpendicular_to_face"]).describe("Axis creation mode"),
      point1X: z.number().optional().describe("First point X (two_points mode, cm)"),
      point1Y: z.number().optional().describe("First point Y (two_points mode, cm)"),
      point1Z: z.number().optional().describe("First point Z (two_points mode, cm)"),
      point2X: z.number().optional().describe("Second point X (two_points mode, cm)"),
      point2Y: z.number().optional().describe("Second point Y (two_points mode, cm)"),
      point2Z: z.number().optional().describe("Second point Z (two_points mode, cm)"),
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
      value: z.number().describe("Dimension value (cm)"),
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
