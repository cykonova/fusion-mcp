import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { FusionBridge } from "../bridge/fusion-bridge.js";
import { registerViewportTools } from "./viewport.js";
import { registerSceneTools } from "./scene.js";
import { registerSketchTools } from "./sketch.js";
import { registerModelingTools } from "./modeling.js";
import { registerDocumentTools } from "./document.js";
import { registerSculptingTools } from "./sculpting.js";
import { registerConstructionTools } from "./construction.js";
import { registerParameterTools } from "./parameters.js";
import { registerAnalysisTools } from "./analysis.js";
import { registerIterationTools } from "./iteration.js";
import { registerAssemblyTools } from "./assembly.js";
import { registerMaterialTools } from "./material.js";

export function registerTools(server: McpServer, bridge: FusionBridge): void {
  registerViewportTools(server, bridge);
  registerSceneTools(server, bridge);
  registerSketchTools(server, bridge);
  registerModelingTools(server, bridge);
  registerSculptingTools(server, bridge);
  registerConstructionTools(server, bridge);
  registerParameterTools(server, bridge);
  registerAnalysisTools(server, bridge);
  registerIterationTools(server, bridge);
  registerAssemblyTools(server, bridge);
  registerMaterialTools(server, bridge);
  registerDocumentTools(server, bridge);
}
