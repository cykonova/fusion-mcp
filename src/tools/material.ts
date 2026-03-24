import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";

export function registerMaterialTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_set_material", {
    description: "Assign a physical material (e.g. ABS, Aluminum, Carbon Fiber) to a body. Affects mass, density, and center-of-gravity calculations. Use fusion_mass_properties to verify changes.",
    inputSchema: {
      bodyId: z.string().describe("Body name or entity token"),
      materialName: z.string().describe("Material name from Fusion library (e.g. 'ABS Plastic', 'Aluminum', 'Steel', 'Carbon Fiber')"),
    },
  }, async (args) => {
    const result = await bridge.call("material.set_material", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_set_appearance", {
    description: "Set the visual appearance of a body. Either pick a named appearance from the library, or specify an RGB color directly. Use to color-code parts by subsystem.",
    inputSchema: {
      bodyId: z.string().describe("Body name or entity token"),
      appearanceName: z.string().optional().describe("Named appearance from Fusion library (e.g. 'Paint - Enamel Glossy (White)')"),
      colorR: z.coerce.number().optional().describe("Red (0-255)"),
      colorG: z.coerce.number().optional().describe("Green (0-255)"),
      colorB: z.coerce.number().optional().describe("Blue (0-255)"),
      colorOpacity: z.coerce.number().optional().describe("Opacity (0-255, default 255)"),
    },
  }, async (args) => {
    const { colorR, colorG, colorB, colorOpacity, ...rest } = args;
    const params: Record<string, unknown> = { ...rest };
    if (colorR !== undefined || colorG !== undefined || colorB !== undefined) {
      params.color = {
        r: colorR ?? 128,
        g: colorG ?? 128,
        b: colorB ?? 128,
        opacity: colorOpacity ?? 255,
      };
    }
    const result = await bridge.call("material.set_appearance", params);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
