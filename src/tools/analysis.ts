import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";

export function registerAnalysisTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_mass_properties", {
    description: "Get physical properties (volume, area, mass, density, center of mass, bounding box) for one or all bodies. Essential for weight distribution and bipedal stability analysis.",
    inputSchema: {
      bodyId: z.string().optional().describe("Body name or entity token. Omit to get properties for all bodies."),
    },
  }, async (args) => {
    const result = await bridge.call("analysis.mass_properties", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_interference_check", {
    description: "Check for interference (overlap) between two or more bodies. Use to verify parts fit together without collision — e.g. ensuring a servo fits inside a forearm cavity.",
    inputSchema: {
      bodyIds: z.array(z.string()).min(2).describe("Body names or entity tokens to check (minimum 2)"),
    },
  }, async (args) => {
    const result = await bridge.call("analysis.interference_check", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_section_analysis", {
    description: "Create a section cut through the model at a given plane and offset. Creates a construction plane at the cut position — use fusion_screenshot to view the cross-section visually.",
    inputSchema: {
      plane: z.enum(["xy", "xz", "yz"]).optional().describe("Standard plane to cut along"),
      planeId: z.string().optional().describe("Construction plane entity token (alternative to plane)"),
      offset: z.coerce.number().default(0).describe("Offset distance from the plane (cm)"),
    },
  }, async (args) => {
    const result = await bridge.call("analysis.section_analysis", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
