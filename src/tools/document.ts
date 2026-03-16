import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";

export function registerDocumentTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_new_document", {
    description: "Create a new Fusion 360 design document",
    inputSchema: {
      name: z.string().optional().describe("Document name"),
    },
  }, async ({ name }) => {
    const result = await bridge.call("document.new", { name });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_save", {
    description: "Save the current Fusion 360 document",
  }, async () => {
    const result = await bridge.call("document.save");
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_export", {
    description: "Export the active design to a file format (STEP, STL, F3D, etc.)",
    inputSchema: {
      format: z.enum(["step", "stl", "f3d", "iges", "sat", "smt"]).describe("Export format"),
      outputPath: z.string().describe("Output file path"),
    },
  }, async (args) => {
    const result = await bridge.call("document.export", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
