import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";

export function registerModelingTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_extrude", {
    description: "Extrude a sketch profile to create a 3D body. Distance is in cm. Use symmetric for centered extrusions.",
    inputSchema: {
      sketchId: z.string().describe("Sketch ID containing the profile"),
      profileIndex: z.coerce.number().default(0).describe("Profile index within the sketch"),
      distance: z.coerce.number().describe("Extrusion distance (cm)"),
      symmetric: z.boolean().default(false).describe("Extrude symmetrically in both directions"),
      operation: z.enum(["new_body", "join", "cut", "intersect"]).default("new_body")
        .describe("Boolean operation type"),
      targetBodyId: z.string().optional().describe("Target body for join/cut/intersect operations"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.extrude", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_revolve", {
    description: "Revolve a sketch profile around an axis to create a 3D body",
    inputSchema: {
      sketchId: z.string().describe("Sketch ID containing the profile"),
      profileIndex: z.coerce.number().default(0).describe("Profile index"),
      axisId: z.string().describe("Axis ID (sketch line or construction axis)"),
      angle: z.coerce.number().default(360).describe("Revolution angle in degrees"),
      operation: z.enum(["new_body", "join", "cut", "intersect"]).default("new_body")
        .describe("Boolean operation type"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.revolve", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_fillet", {
    description: "Apply a fillet (rounded edge) to one or more edges",
    inputSchema: {
      edgeIds: z.array(z.string()).min(1).describe("Edge IDs to fillet"),
      radius: z.coerce.number().describe("Fillet radius (cm)"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.fillet", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_chamfer", {
    description: "Apply a chamfer (beveled edge) to one or more edges",
    inputSchema: {
      edgeIds: z.array(z.string()).min(1).describe("Edge IDs to chamfer"),
      distance: z.coerce.number().describe("Chamfer distance (cm)"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.chamfer", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
