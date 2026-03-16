import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";

export function registerSketchTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_create_sketch", {
    description: "Create a new sketch on a standard plane, construction plane, or planar face",
    inputSchema: {
      plane: z.enum(["xy", "xz", "yz"]).optional().describe("Standard construction plane"),
      constructionPlaneId: z.string().optional().describe("Construction plane name or ID (e.g. 'Plane1' from offset/angle tools)"),
      faceId: z.string().optional().describe("Planar face ID to sketch on"),
      componentId: z.string().optional().describe("Component ID (defaults to root)"),
    },
  }, async (args) => {
    const result = await bridge.call("sketch.create", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_sketch_line", {
    description: "Add a line to a sketch between two points. Coordinates are in cm.",
    inputSchema: {
      sketchId: z.string().describe("Sketch ID"),
      startX: z.coerce.number().describe("Start X (cm)"),
      startY: z.coerce.number().describe("Start Y (cm)"),
      endX: z.coerce.number().describe("End X (cm)"),
      endY: z.coerce.number().describe("End Y (cm)"),
    },
  }, async (args) => {
    const result = await bridge.call("sketch.line", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_sketch_circle", {
    description: "Add a circle to a sketch. Coordinates are in cm.",
    inputSchema: {
      sketchId: z.string().describe("Sketch ID"),
      centerX: z.coerce.number().describe("Center X (cm)"),
      centerY: z.coerce.number().describe("Center Y (cm)"),
      radius: z.coerce.number().describe("Radius (cm)"),
    },
  }, async (args) => {
    const result = await bridge.call("sketch.circle", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_sketch_rectangle", {
    description: "Add a rectangle to a sketch defined by two corner points. Coordinates are in cm.",
    inputSchema: {
      sketchId: z.string().describe("Sketch ID"),
      x1: z.coerce.number().describe("First corner X (cm)"),
      y1: z.coerce.number().describe("First corner Y (cm)"),
      x2: z.coerce.number().describe("Second corner X (cm)"),
      y2: z.coerce.number().describe("Second corner Y (cm)"),
    },
  }, async (args) => {
    const result = await bridge.call("sketch.rectangle", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_sketch_arc", {
    description: "Add an arc to a sketch. Use 3-point mode (start, mid, end) or center-point mode (center, start, sweep angle).",
    inputSchema: {
      sketchId: z.string().describe("Sketch ID"),
      mode: z.enum(["three_point", "center_point"]).describe("Arc creation mode"),
      startX: z.coerce.number().describe("Start point X (cm)"),
      startY: z.coerce.number().describe("Start point Y (cm)"),
      midOrCenterX: z.coerce.number().describe("Mid point X (three_point) or center X (center_point) in cm"),
      midOrCenterY: z.coerce.number().describe("Mid point Y (three_point) or center Y (center_point) in cm"),
      endXOrSweep: z.coerce.number().describe("End point X in cm (three_point) or sweep angle in degrees (center_point)"),
      endY: z.coerce.number().optional().describe("End point Y in cm (three_point mode only)"),
    },
  }, async (args) => {
    const result = await bridge.call("sketch.arc", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_sketch_spline", {
    description: "Add a spline through a series of control points",
    inputSchema: {
      sketchId: z.string().describe("Sketch ID"),
      points: z.array(z.object({
        x: z.coerce.number().describe("X coordinate (cm)"),
        y: z.coerce.number().describe("Y coordinate (cm)"),
      })).min(2).describe("Control points for the spline"),
    },
  }, async (args) => {
    const result = await bridge.call("sketch.spline", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_get_sketch_profiles", {
    description: "List the closed profiles in a sketch. Profiles are needed for extrude, revolve, etc.",
    inputSchema: {
      sketchId: z.string().describe("Sketch ID"),
    },
  }, async ({ sketchId }) => {
    const result = await bridge.call("sketch.getProfiles", { sketchId });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_finish_sketch", {
    description: "Finish/close the active sketch, returning to model space",
    inputSchema: {
      sketchId: z.string().describe("Sketch ID"),
    },
  }, async ({ sketchId }) => {
    const result = await bridge.call("sketch.finish", { sketchId });
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
