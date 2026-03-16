import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";

export function registerSculptingTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_loft", {
    description: "Loft between two or more sketch profiles to create a blended 3D body. Essential for tapered limb segments, torso shaping, and organic transitions between cross-sections.",
    inputSchema: {
      sketchIds: z.array(z.string()).min(2).describe("Sketch IDs containing profiles to loft between (in order)"),
      profileIndices: z.array(z.number()).optional()
        .describe("Profile index for each sketch (defaults to 0 for each)"),
      operation: z.enum(["new_body", "join", "cut", "intersect"]).default("new_body")
        .describe("Boolean operation type"),
      isSolid: z.boolean().default(true).describe("Create solid (true) or surface (false)"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.loft", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_sweep", {
    description: "Sweep a sketch profile along a path to create a 3D body. Use for wiring channels, curved frame rails, and tube-like structures.",
    inputSchema: {
      profileSketchId: z.string().describe("Sketch ID containing the profile to sweep"),
      profileIndex: z.number().default(0).describe("Profile index within the sketch"),
      pathSketchId: z.string().describe("Sketch ID containing the sweep path"),
      pathCurveIndex: z.number().default(0).describe("Curve index in the path sketch"),
      operation: z.enum(["new_body", "join", "cut", "intersect"]).default("new_body")
        .describe("Boolean operation type"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.sweep", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_shell", {
    description: "Hollow out a solid body with uniform wall thickness. Select faces to remove (open faces). Essential for creating enclosures and cavities for electronics.",
    inputSchema: {
      bodyId: z.string().describe("Body ID to shell"),
      thickness: z.number().describe("Wall thickness (cm)"),
      removeFaceIds: z.array(z.string()).optional()
        .describe("Face IDs to remove (creates openings). Omit to shell without openings."),
    },
  }, async (args) => {
    const result = await bridge.call("feature.shell", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_mirror", {
    description: "Mirror bodies or features across a plane. Essential for bilateral symmetry — design one side, mirror to get the other.",
    inputSchema: {
      entityIds: z.array(z.string()).min(1).describe("Body or feature IDs to mirror"),
      mirrorPlane: z.enum(["xy", "xz", "yz"]).optional()
        .describe("Standard plane to mirror across"),
      mirrorPlaneId: z.string().optional()
        .describe("Construction plane or face ID to mirror across (alternative to mirrorPlane)"),
      operation: z.enum(["new_body", "join"]).default("new_body")
        .describe("Create new bodies or join with existing"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.mirror", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_pattern_rectangular", {
    description: "Create a rectangular pattern of bodies or features. Use for mounting hole arrays, vent grilles, sensor arrays.",
    inputSchema: {
      entityIds: z.array(z.string()).min(1).describe("Body or feature IDs to pattern"),
      directionOneAxis: z.enum(["x", "y", "z"]).describe("First direction axis"),
      directionOneCount: z.number().min(1).describe("Number of instances in first direction"),
      directionOneSpacing: z.number().describe("Spacing between instances in first direction (cm)"),
      directionTwoAxis: z.enum(["x", "y", "z"]).optional().describe("Second direction axis"),
      directionTwoCount: z.number().optional().describe("Number of instances in second direction"),
      directionTwoSpacing: z.number().optional().describe("Spacing in second direction (cm)"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.pattern_rectangular", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_pattern_circular", {
    description: "Create a circular pattern of bodies or features around an axis. Use for bolt circles, radial vents, gear teeth.",
    inputSchema: {
      entityIds: z.array(z.string()).min(1).describe("Body or feature IDs to pattern"),
      axisId: z.string().describe("Construction axis or edge ID to pattern around"),
      count: z.number().min(2).describe("Total number of instances (including original)"),
      totalAngle: z.number().default(360).describe("Total angle to distribute instances over (degrees)"),
    },
  }, async (args) => {
    const result = await bridge.call("feature.pattern_circular", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
