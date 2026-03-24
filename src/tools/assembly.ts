import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { FusionBridge } from "../bridge/fusion-bridge.js";

export function registerAssemblyTools(server: McpServer, bridge: FusionBridge): void {

  server.registerTool("fusion_create_joint", {
    description: "Create a joint between two component occurrences. Joints define how parts move relative to each other — revolute for hinges, rigid for fixed connections, slider for linear motion.",
    inputSchema: {
      occurrenceId1: z.string().describe("First occurrence name or entity token"),
      occurrenceId2: z.string().describe("Second occurrence name or entity token"),
      jointType: z.enum(["rigid", "revolute", "slider", "cylindrical", "pin_slot", "planar", "ball"])
        .default("rigid").describe("Type of joint motion"),
      offsetX: z.coerce.number().optional().describe("Joint origin offset X (cm)"),
      offsetY: z.coerce.number().optional().describe("Joint origin offset Y (cm)"),
      offsetZ: z.coerce.number().optional().describe("Joint origin offset Z (cm)"),
    },
  }, async (args) => {
    // Reconstruct nested offset for the Python handler
    const { offsetX, offsetY, offsetZ, ...rest } = args;
    const params: Record<string, unknown> = { ...rest };
    if (offsetX !== undefined || offsetY !== undefined || offsetZ !== undefined) {
      params.offset = { x: offsetX ?? 0, y: offsetY ?? 0, z: offsetZ ?? 0 };
    }
    const result = await bridge.call("assembly.create_joint", params);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_list_joints", {
    description: "List all joints in the design including their type, connected occurrences, lock state, and motion values.",
    inputSchema: {},
  }, async (args) => {
    const result = await bridge.call("assembly.list_joints", args);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });

  server.registerTool("fusion_move_component", {
    description: "Move a component occurrence by translation and/or rotation. Use to position parts in an assembly before creating joints.",
    inputSchema: {
      occurrenceId: z.string().describe("Occurrence name or entity token"),
      translateX: z.coerce.number().optional().describe("Translation X (cm)"),
      translateY: z.coerce.number().optional().describe("Translation Y (cm)"),
      translateZ: z.coerce.number().optional().describe("Translation Z (cm)"),
      rotationAxis: z.enum(["x", "y", "z"]).optional().describe("Axis to rotate around"),
      rotationAngle: z.coerce.number().optional().describe("Rotation angle (degrees)"),
    },
  }, async (args) => {
    // Reconstruct nested objects for the Python handler
    const { translateX, translateY, translateZ, rotationAxis, rotationAngle, ...rest } = args;
    const params: Record<string, unknown> = { ...rest };
    if (translateX !== undefined || translateY !== undefined || translateZ !== undefined) {
      params.translation = { x: translateX ?? 0, y: translateY ?? 0, z: translateZ ?? 0 };
    }
    if (rotationAxis !== undefined && rotationAngle !== undefined) {
      params.rotation = { axis: rotationAxis, angle: rotationAngle };
    }
    const result = await bridge.call("assembly.move_component", params);
    return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
  });
}
