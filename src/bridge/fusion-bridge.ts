/**
 * Bridge to communicate with the Fusion 360 companion add-in.
 *
 * The companion add-in runs a lightweight HTTP server inside Fusion 360's
 * Python environment. This bridge sends typed commands and receives responses.
 *
 * TODO: Implement the companion add-in (Python side)
 * TODO: Add WebSocket support for real-time events from Fusion
 */

export interface BridgeResponse {
  success: boolean;
  data?: unknown;
  error?: string;
}

export class FusionBridge {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl ?? process.env.FUSION_BRIDGE_URL ?? "http://localhost:8765";
  }

  async call(method: string, params?: Record<string, unknown>): Promise<BridgeResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ method, params: params ?? {} }),
      });

      if (!response.ok) {
        return {
          success: false,
          error: `Fusion bridge returned ${response.status}: ${response.statusText}`,
        };
      }

      return await response.json() as BridgeResponse;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);

      if (message.includes("ECONNREFUSED")) {
        return {
          success: false,
          error: "Cannot connect to Fusion 360. Is the companion add-in running?",
        };
      }

      return { success: false, error: message };
    }
  }

  async ping(): Promise<boolean> {
    const result = await this.call("ping");
    return result.success;
  }
}
