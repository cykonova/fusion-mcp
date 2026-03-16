import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";

export function registerViewportTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_screenshot", {
    description: "Capture a screenshot of the current Fusion 360 viewport. Returns a base64-encoded PNG.",
  }, async () => {
    const result = await bridge.call("viewport.screenshot");
    if (result.success && result.data) {
      return {
        content: [{
          type: "image",
          data: result.data as string,
          mimeType: "image/png",
        }],
      };
    }
    return { content: [{ type: "text", text: result.error ?? "Screenshot failed" }], isError: true };
  });

  server.registerTool("fusion_set_view", {
    description: "Set the viewport camera to a named view or custom eye/target position",
    inputSchema: {
      named: z.enum([
        "front", "back", "left", "right", "top", "bottom", "iso",
      ]).optional().describe("Named standard view"),
      eye: z.object({
        x: z.coerce.number(), y: z.coerce.number(), z: z.coerce.number(),
      }).optional().describe("Custom camera eye position"),
      target: z.object({
        x: z.coerce.number(), y: z.coerce.number(), z: z.coerce.number(),
      }).optional().describe("Custom camera target position"),
    },
  }, async ({ named, eye, target }) => {
    const result = await bridge.call("viewport.setView", { named, eye, target });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_zoom_to_fit", {
    description: "Fit all geometry in the viewport, or zoom to a specific body/component",
    inputSchema: {
      entityId: z.string().optional().describe("Body or component ID to zoom to (omit for fit-all)"),
    },
  }, async ({ entityId }) => {
    const result = await bridge.call("viewport.zoomToFit", { entityId });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_set_visual_style", {
    description: "Set the viewport visual style (shaded, wireframe, or wireframe on shaded for seeing internal structure)",
    inputSchema: {
      style: z.enum(["shaded", "wireframe", "shaded_wireframe"]).describe("Visual style"),
    },
  }, async ({ style }) => {
    const result = await bridge.call("viewport.setVisualStyle", { style });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_toggle_visibility", {
    description: "Show or hide a specific body or component",
    inputSchema: {
      entityId: z.string().describe("Body or component ID"),
      visible: z.boolean().describe("Whether to show (true) or hide (false)"),
    },
  }, async ({ entityId, visible }) => {
    const result = await bridge.call("viewport.toggleVisibility", { entityId, visible });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_orbit", {
    description: "Rotate the viewport camera by delta angles (degrees) for fine-tuning a view",
    inputSchema: {
      deltaYaw: z.coerce.number().default(0).describe("Horizontal rotation in degrees"),
      deltaPitch: z.coerce.number().default(0).describe("Vertical rotation in degrees"),
    },
  }, async ({ deltaYaw, deltaPitch }) => {
    const result = await bridge.call("viewport.orbit", { deltaYaw, deltaPitch });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
