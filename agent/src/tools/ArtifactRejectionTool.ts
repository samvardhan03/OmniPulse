/**
 * src/tools/ArtifactRejectionTool.ts
 * -----------------------------------
 * Identifies and flags corrupted or artifact-laden signals based on
 * variance analysis of the Wavelet Scattering Transform output.
 *
 * Supports two rejection strategies:
 *   1. **Static threshold**: flag paths with variance > fixed value
 *   2. **Statistical outlier** (mean + n_sigma × std): domain-agnostic
 *      approach that auto-adapts to the signal's own statistics.
 */

import type { WSTResult, EvaluationConfig } from "@mcp/schemas";
import { EvaluationConfigSchema } from "@mcp/schemas";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ArtifactRejectionResult {
  /** Whether any artifacts were detected. */
  hasArtifacts: boolean;

  /** Indices of scattering paths flagged as outliers. */
  flaggedPaths: number[];

  /** The threshold that was applied (static or computed). */
  appliedThreshold: number;

  /** Strategy used: "static" or "statistical". */
  strategy: "static" | "statistical";

  /** Human-readable recommendation for the QueryEngine. */
  recommendation: string;
}

// ── Implementation ────────────────────────────────────────────────────────────

/**
 * Analyse WST variance metadata and flag artifact-contaminated paths.
 *
 * @param wstResult  - Parsed result from the execute_wst MCP tool.
 * @param config     - Evaluation config with threshold settings.
 *                     Accepts raw object (will be validated via Zod).
 * @returns            Structured rejection result with recommendations.
 */
export function rejectArtifacts(
  wstResult: WSTResult,
  config?: Partial<EvaluationConfig>,
): ArtifactRejectionResult {
  const evalConfig = EvaluationConfigSchema.parse(config ?? {});
  const { variance } = wstResult;

  if (variance.length === 0) {
    return {
      hasArtifacts: false,
      flaggedPaths: [],
      appliedThreshold: 0,
      strategy: "statistical",
      recommendation: "No variance data available — skipping artifact analysis.",
    };
  }

  let threshold: number;
  let strategy: "static" | "statistical";

  if (evalConfig.variance_threshold !== null) {
    // ── Static threshold mode ──────────────────────────────────────
    threshold = evalConfig.variance_threshold;
    strategy = "static";
  } else {
    // ── Statistical outlier mode (mean + n_sigma × std) ────────────
    const mean = variance.reduce((a, b) => a + b, 0) / variance.length;
    const stdDev = Math.sqrt(
      variance.reduce((acc, v) => acc + (v - mean) ** 2, 0) / variance.length,
    );
    threshold = mean + evalConfig.variance_n_sigma * stdDev;
    strategy = "statistical";
  }

  const flaggedPaths = variance
    .map((v, i) => (v > threshold ? i : -1))
    .filter((i) => i >= 0);

  const hasArtifacts = flaggedPaths.length > 0;

  let recommendation: string;
  if (!hasArtifacts) {
    recommendation =
      "Signal quality is within acceptable bounds. No artifact rejection needed.";
  } else {
    recommendation =
      `ARTIFACT DETECTED: ${flaggedPaths.length} scattering path(s) exceed ` +
      `the ${strategy} variance threshold (${threshold.toExponential(2)}). ` +
      `Flagged paths: [${flaggedPaths.join(", ")}]. ` +
      `Recommendation: purge corrupted epochs and re-run WST.`;
  }

  return {
    hasArtifacts,
    flaggedPaths,
    appliedThreshold: threshold,
    strategy,
    recommendation,
  };
}
