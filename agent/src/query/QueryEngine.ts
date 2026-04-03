/**
 * src/query/QueryEngine.ts
 * -------------------------
 * Autonomous evaluation logic for the Agentic-Wavelet pipeline.
 *
 * The QueryEngine parses the structured JSON result from the Python
 * MCP server, applies configurable heuristic rules, and deterministically
 * decides the next pipeline action — without human intervention.
 *
 * Decision tree:
 *   1. Parse JSON → Zod validation
 *   2. null_count > 0         →  flag DATA_CORRUPTION
 *   3. Variance outliers      →  recommend ARTIFACT_REJECTION
 *   4. SNR < min_snr_db       →  recommend DENOISING
 *   5. All checks pass        →  APPROVE for downstream tokenization
 */

import {
  WSTResultSchema,
  EvaluationConfigSchema,
  type WSTResult,
  type EvaluationConfig,
} from "@mcp/schemas";
import { rejectArtifacts, type ArtifactRejectionResult } from "@tools/ArtifactRejectionTool";

// ── Decision types ────────────────────────────────────────────────────────────

export type PipelineAction =
  | "APPROVE_FOR_TOKENIZATION"
  | "ARTIFACT_REJECTION"
  | "SECONDARY_DENOISING"
  | "DATA_CORRUPTION_HALT";

export interface EvaluationVerdict {
  /** The autonomous decision. */
  action: PipelineAction;
  /** Human-readable explanation of the decision. */
  reasoning: string;
  /** Parsed WST result (null if parsing failed). */
  wstResult: WSTResult | null;
  /** Artifact rejection details (null if not triggered). */
  artifactAnalysis: ArtifactRejectionResult | null;
  /** Whether the evaluation encountered any errors. */
  hasErrors: boolean;
  /** Error message if evaluation itself failed. */
  error?: string;
}

// ── QueryEngine ───────────────────────────────────────────────────────────────

/**
 * Evaluate the result from the WST MCP tool and produce an
 * autonomous pipeline decision.
 *
 * @param rawJson      - Raw JSON string from the MCP server response.
 * @param configInput  - Optional evaluation config overrides.
 *                       Supports dynamic variance thresholds.
 * @returns              Structured verdict with action and reasoning.
 */
export function evaluateWSTResult(
  rawJson: string,
  configInput?: Partial<EvaluationConfig>,
): EvaluationVerdict {
  // ── 1. Parse evaluation config ──────────────────────────────────────
  let evalConfig: EvaluationConfig;
  try {
    evalConfig = EvaluationConfigSchema.parse(configInput ?? {});
  } catch (err) {
    return {
      action: "DATA_CORRUPTION_HALT",
      reasoning: `Invalid evaluation config: ${err instanceof Error ? err.message : String(err)}`,
      wstResult: null,
      artifactAnalysis: null,
      hasErrors: true,
      error: "Config validation failed",
    };
  }

  // ── 2. Parse raw JSON through Zod ───────────────────────────────────
  let parsed: unknown;
  try {
    parsed = JSON.parse(rawJson);
  } catch {
    return {
      action: "DATA_CORRUPTION_HALT",
      reasoning: `Failed to parse MCP response as JSON: ${rawJson.slice(0, 200)}`,
      wstResult: null,
      artifactAnalysis: null,
      hasErrors: true,
      error: "JSON parse error",
    };
  }

  const zodResult = WSTResultSchema.safeParse(parsed);
  if (!zodResult.success) {
    const issues = zodResult.error.issues
      .map((i) => `${i.path.join(".")}: ${i.message}`)
      .join("; ");
    return {
      action: "DATA_CORRUPTION_HALT",
      reasoning: `WST result schema validation failed: ${issues}`,
      wstResult: null,
      artifactAnalysis: null,
      hasErrors: true,
      error: "Schema validation failed",
    };
  }

  const wstResult = zodResult.data;

  // ── 3. Check for data corruption (NaN/Inf) ──────────────────────────
  if (wstResult.null_count > evalConfig.max_null_count) {
    return {
      action: "DATA_CORRUPTION_HALT",
      reasoning:
        `DATA CORRUPTION: ${wstResult.null_count} NaN/Inf values detected in ` +
        `scattering output. Maximum allowed: ${evalConfig.max_null_count}. ` +
        `Pipeline halted — investigate raw input integrity.`,
      wstResult,
      artifactAnalysis: null,
      hasErrors: true,
    };
  }

  // ── 4. Variance outlier analysis (artifact rejection) ───────────────
  const artifactAnalysis = rejectArtifacts(wstResult, evalConfig);

  if (artifactAnalysis.hasArtifacts) {
    return {
      action: "ARTIFACT_REJECTION",
      reasoning: artifactAnalysis.recommendation,
      wstResult,
      artifactAnalysis,
      hasErrors: false,
    };
  }

  // ── 5. SNR check ────────────────────────────────────────────────────
  if (wstResult.snr_db < evalConfig.min_snr_db) {
    return {
      action: "SECONDARY_DENOISING",
      reasoning:
        `Low signal quality: SNR = ${wstResult.snr_db.toFixed(2)} dB is below ` +
        `the minimum threshold of ${evalConfig.min_snr_db} dB. ` +
        `Recommendation: apply secondary denoising filters before proceeding.`,
      wstResult,
      artifactAnalysis,
      hasErrors: false,
    };
  }

  // ── 6. All checks passed — approve ──────────────────────────────────
  return {
    action: "APPROVE_FOR_TOKENIZATION",
    reasoning:
      `Signal quality APPROVED. SNR = ${wstResult.snr_db.toFixed(2)} dB, ` +
      `${wstResult.n_files_processed} file(s) processed, ` +
      `output shape = [${wstResult.output_shape.join(", ")}], ` +
      `null count = ${wstResult.null_count}. ` +
      `Ready for downstream TFM-tokenization and TF-C alignment.`,
    wstResult,
    artifactAnalysis,
    hasErrors: false,
  };
}
