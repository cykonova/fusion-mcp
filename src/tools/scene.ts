import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";
import { zBool } from "./schema.js";

export function registerSceneTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_get_document_info", {
    description: "Get information about the currently active Fusion 360 document (name, units, saved state, file path)",
  }, async () => {
    const result = await bridge.call("document.info");
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_create_component", {
    description: "Create a new empty component in the design. Returns the component and its occurrence — use the occurrence name/token for assembly operations (joints, move).",
    inputSchema: {
      name: z.string().optional().describe("Component name (e.g. 'UpperArm', 'ServoMount')"),
    },
  }, async (args) => {
    const result = await bridge.call("component.create", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_list_components", {
    description: "List all components in the active design hierarchy with names, IDs, and nesting",
  }, async () => {
    const result = await bridge.call("component.list");
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_list_bodies", {
    description: "List all bodies in a component (name, ID, volume, bounding box). Use includeFaces to get face entity tokens needed for shell and other face-based operations.",
    inputSchema: {
      componentId: z.string().optional().describe("Component ID (defaults to root component)"),
      includeFaces: zBool().optional().describe("Include face details (entity tokens, area, geometry type, centroid) for each body"),
    },
  }, async ({ componentId, includeFaces }) => {
    const result = await bridge.call("component.listBodies", { componentId, includeFaces });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_get_timeline", {
    description: "Get the feature timeline showing what was built and in what order",
  }, async () => {
    const result = await bridge.call("timeline.get");
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_measure", {
    description: "Measure distance or angle between two entities, or get mass properties of a body",
    inputSchema: {
      entityId1: z.string().describe("First entity ID"),
      entityId2: z.string().optional().describe("Second entity ID (omit for mass properties of first entity)"),
    },
  }, async ({ entityId1, entityId2 }) => {
    const result = await bridge.call("scene.measure", { entityId1, entityId2 });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
