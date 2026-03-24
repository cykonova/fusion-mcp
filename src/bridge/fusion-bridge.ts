/**
 * Bridge to communicate with the Fusion 360 companion add-in.
 *
 * The companion add-in runs a lightweight HTTP server inside Fusion 360's
 * Python environment. This bridge sends typed commands and receives responses.
 */

import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

export interface BridgeResponse {
  success: boolean;
  data?: unknown;
  error?: string;
}

const DEFAULT_FUSION_PATH_MACOS = join(
  homedir(),
  "Library/Application Support/Autodesk/webdeploy/production/Autodesk Fusion 360.app",
);

export class FusionBridge {
  private baseUrl: string;
  private launchTimeout: number;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl ?? process.env.FUSION_BRIDGE_URL ?? "http://localhost:8765";
    this.launchTimeout = parseInt(process.env.FUSION_LAUNCH_TIMEOUT ?? "60", 10) * 1000;
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
          error: "Cannot connect to Fusion 360. Is the companion add-in running? Use fusion_launch to start Fusion.",
        };
      }

      return { success: false, error: message };
    }
  }

  async ping(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, { signal: AbortSignal.timeout(3000) });
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Check if Fusion 360's companion add-in is reachable.
   */
  async isRunning(): Promise<boolean> {
    return this.ping();
  }

  /**
   * Launch Fusion 360 and wait for the companion add-in to become healthy.
   * Returns true if Fusion is already running or successfully launched.
   */
  async ensureRunning(): Promise<BridgeResponse> {
    if (await this.isRunning()) {
      return { success: true, data: { status: "already_running" } };
    }

    const fusionPath = process.env.FUSION360_PATH ?? DEFAULT_FUSION_PATH_MACOS;

    if (!existsSync(fusionPath)) {
      return {
        success: false,
        error: `Fusion 360 not found at '${fusionPath}'. Set FUSION360_PATH env var to the correct location.`,
      };
    }

    // Launch Fusion 360
    try {
      execFile("open", ["-a", fusionPath], (err) => {
        if (err) {
          console.error(`Failed to launch Fusion 360: ${err.message}`);
        }
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { success: false, error: `Failed to launch Fusion 360: ${message}` };
    }

    // Poll for the add-in to become healthy
    const startTime = Date.now();
    const pollInterval = 2000;

    while (Date.now() - startTime < this.launchTimeout) {
      await new Promise(resolve => setTimeout(resolve, pollInterval));

      if (await this.isRunning()) {
        return {
          success: true,
          data: {
            status: "launched",
            waitTime: Math.round((Date.now() - startTime) / 1000),
          },
        };
      }
    }

    return {
      success: false,
      error: `Fusion 360 launched but companion add-in did not respond within ${this.launchTimeout / 1000}s. Ensure the FusionMCPBridge add-in is installed and enabled.`,
    };
  }
}
