import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";
import { zBool } from "./schema.js";

export function registerDocumentTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_launch", {
    description: "Launch Fusion 360 and wait for the companion add-in to become ready. If Fusion is already running, returns immediately. Use this before other tools if Fusion might not be running.",
  }, async () => {
    const result = await bridge.ensureRunning();
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_list_documents", {
    description: "List all open Fusion 360 documents with their names, save status, and which is active.",
  }, async () => {
    const result = await bridge.call("document.list_documents");
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_activate_document", {
    description: "Switch to a different open Fusion 360 document by name. Use fusion_list_documents to see available documents.",
    inputSchema: {
      name: z.string().describe("Document name to activate"),
    },
  }, async (args) => {
    const result = await bridge.call("document.activate", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_close_document", {
    description: "Close a Fusion 360 document by name, or the active document if no name given.",
    inputSchema: {
      name: z.string().optional().describe("Document name to close (defaults to active document)"),
      save: zBool().default(false).describe("Save before closing"),
    },
  }, async (args) => {
    const result = await bridge.call("document.close", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_open_document", {
    description: "Open a Fusion 360 document from a local file path. Supports .f3d, .f3z, .step, .stp, .iges, .igs, .sat, .smt, .stl files.",
    inputSchema: {
      filePath: z.string().describe("Path to the file to open"),
    },
  }, async (args) => {
    const result = await bridge.call("document.open", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

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
