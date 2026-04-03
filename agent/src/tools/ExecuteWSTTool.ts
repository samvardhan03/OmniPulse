/**
 * src/tools/ExecuteWSTTool.ts
 * ---------------------------
 * Tool wrapper that sends a Zod-validated payload to the Python
 * transient_wst MCP server and returns a typed WST result.
 *
 * This is the primary compute tool in the agentic pipeline — it
 * triggers the Kymatio Wavelet Scattering Transform on raw
 * time-series data.
 */

import type { McpBridge, McpToolResult } from "@mcp/McpClient";
import {
  ExecuteWSTInputSchema,
  WSTResultSchema,
  type ExecuteWSTInput,
  type WSTResult,
} from "@mcp/schemas";

// ── Result type ───────────────────────────────────────────────────────────────

export interface ExecuteWSTToolResult {
  /** Whether the tool executed successfully. */
  success: boolean;
  /** Parsed, typed WST result (null on failure). */
  data: WSTResult | null;
  /** Error message if execution failed. */
  error?: string;
}

// ── Tool implementation ───────────────────────────────────────────────────────

/**
 * Execute the Wavelet Scattering Transform via the MCP bridge.
 *
 * 1. Validates input against `ExecuteWSTInputSchema`
 * 2. Flattens the `q_wavelets` tuple to `q1`/`q2` for the Python server
 * 3. Sends the payload via `mcpBridge.callTool("execute_wst", ...)`
 * 4. Parses the JSON response through `WSTResultSchema`
 *
 * @param bridge  - Connected MCP bridge instance.
 * @param input   - Raw input (will be validated via Zod).
 * @returns         Typed result with success flag and parsed data.
 */
export async function executeWST(
  bridge: McpBridge,
  input: unknown,
): Promise<ExecuteWSTToolResult> {
  // ── 1. Validate input ────────────────────────────────────────────────
  const parseResult = ExecuteWSTInputSchema.safeParse(input);

  if (!parseResult.success) {
    const issues = parseResult.error.issues
      .map((i) => `${i.path.join(".")}: ${i.message}`)
      .join("; ");
    return {
      success: false,
      data: null,
      error: `Input validation failed: ${issues}`,
    };
  }

  const validated: ExecuteWSTInput = parseResult.data;

  // ── 2. Flatten tuple for Python MCP server ───────────────────────────
  const mcpArgs: Record<string, unknown> = {
    input_directory: validated.input_directory,
    output_directory: validated.output_directory,
    sampling_rate: validated.sampling_rate,
    j_scale: validated.j_scale,
    q1: validated.q_wavelets[0],
    q2: validated.q_wavelets[1],
    apply_pca: validated.apply_pca,
    pca_variance: validated.pca_variance,
  };

  // ── 3. Call MCP tool ─────────────────────────────────────────────────
  let mcpResult: McpToolResult;
  try {
    mcpResult = await bridge.callTool("execute_wst", mcpArgs);
  } catch (err) {
    const msg = err instanceof Error ? err.message : String(err);
    return {
      success: false,
      data: null,
      error: `MCP call failed: ${msg}`,
    };
  }

  if (mcpResult.isError) {
    return {
      success: false,
      data: null,
      error: `MCP server returned error: ${mcpResult.content}`,
    };
  }

  // ── 4. Parse response JSON ───────────────────────────────────────────
  let parsed: unknown;
  try {
    parsed = JSON.parse(mcpResult.content);
  } catch {
    return {
      success: false,
      data: null,
      error: `Failed to parse MCP response as JSON: ${mcpResult.content.slice(0, 200)}`,
    };
  }

  const resultParse = WSTResultSchema.safeParse(parsed);
  if (!resultParse.success) {
    const issues = resultParse.error.issues
      .map((i) => `${i.path.join(".")}: ${i.message}`)
      .join("; ");
    return {
      success: false,
      data: null,
      error: `Response validation failed: ${issues}`,
    };
  }

  return {
    success: true,
    data: resultParse.data,
  };
}
