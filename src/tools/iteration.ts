import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";
import { zBool } from "./schema.js";

export function registerIterationTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_undo", {
    description: "Undo recent operations by moving the timeline marker backward. Use for quick rollback when experimenting with design alternatives.",
    inputSchema: {
      count: z.coerce.number().default(1).describe("Number of steps to undo"),
    },
  }, async (args) => {
    const result = await bridge.call("iteration.undo", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_redo", {
    description: "Redo previously undone operations by moving the timeline marker forward.",
    inputSchema: {
      count: z.coerce.number().default(1).describe("Number of steps to redo"),
    },
  }, async (args) => {
    const result = await bridge.call("iteration.redo", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_suppress_feature", {
    description: "Suppress or unsuppress a feature in the timeline. Suppressed features are temporarily disabled without being deleted — useful for testing design alternatives.",
    inputSchema: {
      featureId: z.string().describe("Feature name or entity token"),
      suppress: zBool().default(true).describe("true to suppress, false to unsuppress"),
    },
  }, async (args) => {
    const result = await bridge.call("iteration.suppress_feature", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_edit_feature", {
    description: "Edit parameters of an existing feature without rebuilding from scratch. Supports extrude (distance), revolve (angle), fillet (radius), and chamfer (distance).",
    inputSchema: {
      featureId: z.string().describe("Feature name or entity token"),
      parameters: z.record(z.string(), z.coerce.number()).describe("Key-value pairs of parameter names to new values (e.g. {\"distance\": 5.0})"),
    },
  }, async (args) => {
    const result = await bridge.call("iteration.edit_feature", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
