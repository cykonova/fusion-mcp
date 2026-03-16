import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";

const bridge = new FusionBridge();

export function registerTools(server: McpServer): void {
  // -- Document Management --

  server.tool(
    "fusion_get_document_info",
    "Get information about the currently active Fusion 360 document",
    {},
    async () => {
      const result = await bridge.call("document.info");
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
  );

  // -- Sketch Operations --

  server.tool(
    "fusion_create_sketch",
    "Create a new sketch on a construction plane",
    {
      plane: z.enum(["xy", "xz", "yz"]).describe("Construction plane to sketch on"),
      component: z.string().optional().describe("Component name (defaults to root)"),
    },
    async ({ plane, component }) => {
      const result = await bridge.call("sketch.create", { plane, component });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    "fusion_add_sketch_line",
    "Add a line to an existing sketch",
    {
      sketchId: z.string().describe("Sketch identifier"),
      startX: z.number().describe("Start point X coordinate (cm)"),
      startY: z.number().describe("Start point Y coordinate (cm)"),
      endX: z.number().describe("End point X coordinate (cm)"),
      endY: z.number().describe("End point Y coordinate (cm)"),
    },
    async ({ sketchId, startX, startY, endX, endY }) => {
      const result = await bridge.call("sketch.addLine", {
        sketchId, startX, startY, endX, endY,
      });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    "fusion_add_sketch_circle",
    "Add a circle to an existing sketch",
    {
      sketchId: z.string().describe("Sketch identifier"),
      centerX: z.number().describe("Center X coordinate (cm)"),
      centerY: z.number().describe("Center Y coordinate (cm)"),
      radius: z.number().describe("Radius (cm)"),
    },
    async ({ sketchId, centerX, centerY, radius }) => {
      const result = await bridge.call("sketch.addCircle", {
        sketchId, centerX, centerY, radius,
      });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    "fusion_add_sketch_rectangle",
    "Add a rectangle to an existing sketch by two corner points",
    {
      sketchId: z.string().describe("Sketch identifier"),
      x1: z.number().describe("First corner X (cm)"),
      y1: z.number().describe("First corner Y (cm)"),
      x2: z.number().describe("Second corner X (cm)"),
      y2: z.number().describe("Second corner Y (cm)"),
    },
    async ({ sketchId, x1, y1, x2, y2 }) => {
      const result = await bridge.call("sketch.addRectangle", {
        sketchId, x1, y1, x2, y2,
      });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
  );

  // -- 3D Operations --

  server.tool(
    "fusion_extrude",
    "Extrude a sketch profile to create a 3D body",
    {
      sketchId: z.string().describe("Sketch containing the profile"),
      profileIndex: z.number().default(0).describe("Profile index within the sketch"),
      distance: z.number().describe("Extrusion distance (cm)"),
      operation: z.enum(["new_body", "join", "cut", "intersect"]).default("new_body")
        .describe("Boolean operation type"),
    },
    async ({ sketchId, profileIndex, distance, operation }) => {
      const result = await bridge.call("feature.extrude", {
        sketchId, profileIndex, distance, operation,
      });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    "fusion_revolve",
    "Revolve a sketch profile around an axis",
    {
      sketchId: z.string().describe("Sketch containing the profile"),
      profileIndex: z.number().default(0).describe("Profile index"),
      axisId: z.string().describe("Axis identifier (sketch line or construction axis)"),
      angle: z.number().default(360).describe("Revolution angle in degrees"),
    },
    async ({ sketchId, profileIndex, axisId, angle }) => {
      const result = await bridge.call("feature.revolve", {
        sketchId, profileIndex, axisId, angle,
      });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    "fusion_fillet",
    "Apply a fillet (round) to edges of a body",
    {
      bodyId: z.string().describe("Body identifier"),
      edgeIds: z.array(z.string()).describe("Edge identifiers to fillet"),
      radius: z.number().describe("Fillet radius (cm)"),
    },
    async ({ bodyId, edgeIds, radius }) => {
      const result = await bridge.call("feature.fillet", {
        bodyId, edgeIds, radius,
      });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
  );

  // -- Component/Body Management --

  server.tool(
    "fusion_list_bodies",
    "List all bodies in the active design or a specific component",
    {
      component: z.string().optional().describe("Component name (defaults to root)"),
    },
    async ({ component }) => {
      const result = await bridge.call("component.listBodies", { component });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
  );

  server.tool(
    "fusion_list_components",
    "List all components in the active design",
    {},
    async () => {
      const result = await bridge.call("component.list");
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
  );

  // -- Export --

  server.tool(
    "fusion_export",
    "Export the active design to a file",
    {
      format: z.enum(["step", "stl", "f3d", "iges", "sat", "smt"]).describe("Export format"),
      outputPath: z.string().describe("Output file path"),
    },
    async ({ format, outputPath }) => {
      const result = await bridge.call("document.export", { format, outputPath });
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    }
  );
}
