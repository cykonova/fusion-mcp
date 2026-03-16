import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { FusionBridge } from "../bridge/fusion-bridge.js";
import { registerViewportTools } from "./viewport.js";
import { registerSceneTools } from "./scene.js";
import { registerSketchTools } from "./sketch.js";
import { registerModelingTools } from "./modeling.js";
import { registerDocumentTools } from "./document.js";

export function registerTools(server: McpServer, bridge: FusionBridge): void {
  registerViewportTools(server, bridge);
  registerSceneTools(server, bridge);
  registerSketchTools(server, bridge);
  registerModelingTools(server, bridge);
  registerDocumentTools(server, bridge);
}
