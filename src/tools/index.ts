import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { FusionBridge } from "../bridge/fusion-bridge.js";
import { registerViewportTools } from "./viewport.js";
import { registerSceneTools } from "./scene.js";
import { registerSketchTools } from "./sketch.js";
import { registerModelingTools } from "./modeling.js";
import { registerDocumentTools } from "./document.js";
import { registerSculptingTools } from "./sculpting.js";
import { registerConstructionTools } from "./construction.js";

export function registerTools(server: McpServer, bridge: FusionBridge): void {
  registerViewportTools(server, bridge);
  registerSceneTools(server, bridge);
  registerSketchTools(server, bridge);
  registerModelingTools(server, bridge);
  registerSculptingTools(server, bridge);
  registerConstructionTools(server, bridge);
  registerDocumentTools(server, bridge);
}
