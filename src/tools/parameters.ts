import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";
import { zBool } from "./schema.js";

export function registerParameterTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_create_parameter", {
    description: "Create a named user parameter for parametric design. Use meaningful names like 'shoulder_width' or 'servo_bore_diameter' so the entire model updates proportionally when values change.",
    inputSchema: {
      name: z.string().describe("Parameter name (e.g. 'forearm_length')"),
      value: z.coerce.number().describe("Numeric value"),
      units: z.string().default("cm").describe("Units (cm, mm, in, deg, etc.)"),
      comment: z.string().optional().describe("Description of what this parameter controls"),
    },
  }, async (args) => {
    const result = await bridge.call("parameter.create", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_update_parameter", {
    description: "Update an existing user parameter's value or expression. Changing a parameter automatically updates all features that reference it.",
    inputSchema: {
      name: z.string().describe("Parameter name to update"),
      value: z.coerce.number().optional().describe("New numeric value"),
      expression: z.string().optional().describe("New expression (e.g. 'shoulder_width / 2')"),
      units: z.string().optional().describe("Units for the new value (defaults to parameter's existing units)"),
      comment: z.string().optional().describe("Updated comment"),
    },
  }, async (args) => {
    const result = await bridge.call("parameter.update", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_list_parameters", {
    description: "List all user-defined parameters and their current values. Optionally include auto-generated model parameters from features.",
    inputSchema: {
      includeModel: zBool().default(false).describe("Include model parameters (auto-generated from features) in addition to user parameters"),
    },
  }, async (args) => {
    const result = await bridge.call("parameter.list_params", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
