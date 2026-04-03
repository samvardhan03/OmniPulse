/**
 * agent/tests/schema_validation.test.ts
 * ---------------------------------------
 * Bun test suite validating the Zod schemas that govern the MCP
 * tool interface.
 *
 * Tests verify:
 *   1. Invalid j_scale values (string, negative, >16) are rejected.
 *   2. Valid parameters are accepted and defaults applied.
 *   3. WSTResultSchema parses sample JSON correctly.
 *   4. EvaluationConfigSchema handles dynamic thresholds.
 *   5. QueryEngine evaluation logic produces correct decisions.
 */

import { describe, test, expect } from "bun:test";
import {
  ExecuteWSTInputSchema,
  WSTResultSchema,
  EvaluationConfigSchema,
} from "../src/mcp/schemas";
import { evaluateWSTResult } from "../src/query/QueryEngine";

// ── ExecuteWSTInputSchema ────────────────────────────────────────────────────

describe("ExecuteWSTInputSchema", () => {
  const validInput = {
    input_directory: "/data/signals",
    output_directory: "/data/output",
    sampling_rate: 256.0,
    j_scale: 8,
    q_wavelets: [8, 1] as [number, number],
    apply_pca: true,
  };

  test("accepts valid parameters", () => {
    const result = ExecuteWSTInputSchema.safeParse(validInput);
    expect(result.success).toBe(true);
  });

  test("applies default values for optional fields", () => {
    const minimal = {
      input_directory: "/data/in",
      output_directory: "/data/out",
      j_scale: 6,
      q_wavelets: [4, 1],
    };
    const result = ExecuteWSTInputSchema.safeParse(minimal);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.sampling_rate).toBe(256.0);
      expect(result.data.apply_pca).toBe(true);
      expect(result.data.pca_variance).toBe(0.95);
    }
  });

  test("rejects j_scale as a string", () => {
    const result = ExecuteWSTInputSchema.safeParse({
      ...validInput,
      j_scale: "eight",
    });
    expect(result.success).toBe(false);
  });

  test("rejects negative j_scale", () => {
    const result = ExecuteWSTInputSchema.safeParse({
      ...validInput,
      j_scale: -1,
    });
    expect(result.success).toBe(false);
  });

  test("rejects j_scale > 16", () => {
    const result = ExecuteWSTInputSchema.safeParse({
      ...validInput,
      j_scale: 17,
    });
    expect(result.success).toBe(false);
  });

  test("rejects j_scale = 0", () => {
    const result = ExecuteWSTInputSchema.safeParse({
      ...validInput,
      j_scale: 0,
    });
    expect(result.success).toBe(false);
  });

  test("rejects fractional j_scale", () => {
    const result = ExecuteWSTInputSchema.safeParse({
      ...validInput,
      j_scale: 4.5,
    });
    expect(result.success).toBe(false);
  });

  test("rejects Q1 = 0", () => {
    const result = ExecuteWSTInputSchema.safeParse({
      ...validInput,
      q_wavelets: [0, 1],
    });
    expect(result.success).toBe(false);
  });

  test("rejects negative sampling_rate", () => {
    const result = ExecuteWSTInputSchema.safeParse({
      ...validInput,
      sampling_rate: -100,
    });
    expect(result.success).toBe(false);
  });

  test("rejects empty input_directory", () => {
    const result = ExecuteWSTInputSchema.safeParse({
      ...validInput,
      input_directory: "",
    });
    expect(result.success).toBe(false);
  });
});

// ── WSTResultSchema ──────────────────────────────────────────────────────────

describe("WSTResultSchema", () => {
  const sampleResult = {
    snr_db: 12.5,
    variance: [0.01, 0.02, 0.015, 0.018],
    null_count: 0,
    n_files_processed: 3,
    output_shape: [2, 120, 16],
    outlier_paths: [],
    pca_applied: true,
    pca_components: 45,
  };

  test("parses valid result JSON", () => {
    const result = WSTResultSchema.safeParse(sampleResult);
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.snr_db).toBe(12.5);
      expect(result.data.variance).toHaveLength(4);
      expect(result.data.pca_components).toBe(45);
    }
  });

  test("handles pca_components = null", () => {
    const result = WSTResultSchema.safeParse({
      ...sampleResult,
      pca_applied: false,
      pca_components: null,
    });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.pca_components).toBeNull();
    }
  });

  test("rejects missing snr_db", () => {
    const { snr_db, ...rest } = sampleResult;
    const result = WSTResultSchema.safeParse(rest);
    expect(result.success).toBe(false);
  });
});

// ── EvaluationConfigSchema ───────────────────────────────────────────────────

describe("EvaluationConfigSchema", () => {
  test("applies defaults when empty", () => {
    const result = EvaluationConfigSchema.parse({});
    expect(result.variance_threshold).toBeNull();
    expect(result.variance_n_sigma).toBe(3.0);
    expect(result.min_snr_db).toBe(3.0);
    expect(result.max_null_count).toBe(0);
  });

  test("accepts static threshold", () => {
    const result = EvaluationConfigSchema.parse({
      variance_threshold: 1e6,
    });
    expect(result.variance_threshold).toBe(1e6);
  });

  test("accepts custom n_sigma", () => {
    const result = EvaluationConfigSchema.parse({
      variance_n_sigma: 2.5,
    });
    expect(result.variance_n_sigma).toBe(2.5);
  });
});

// ── QueryEngine evaluation ───────────────────────────────────────────────────

describe("QueryEngine.evaluateWSTResult", () => {
  const goodResult = JSON.stringify({
    snr_db: 15.0,
    variance: [0.01, 0.02, 0.015, 0.018],
    null_count: 0,
    n_files_processed: 3,
    output_shape: [2, 120, 16],
    outlier_paths: [],
    pca_applied: true,
    pca_components: 45,
  });

  test("approves clean signal for tokenization", () => {
    const verdict = evaluateWSTResult(goodResult);
    expect(verdict.action).toBe("APPROVE_FOR_TOKENIZATION");
    expect(verdict.hasErrors).toBe(false);
  });

  test("halts on null values", () => {
    const corrupted = JSON.stringify({
      snr_db: 10.0,
      variance: [0.01],
      null_count: 5,
      n_files_processed: 1,
      output_shape: [1, 10, 16],
      outlier_paths: [],
      pca_applied: false,
      pca_components: null,
    });
    const verdict = evaluateWSTResult(corrupted);
    expect(verdict.action).toBe("DATA_CORRUPTION_HALT");
  });

  test("recommends denoising for low SNR", () => {
    const lowSnr = JSON.stringify({
      snr_db: 1.5,
      variance: [0.01, 0.01],
      null_count: 0,
      n_files_processed: 1,
      output_shape: [1, 10, 16],
      outlier_paths: [],
      pca_applied: false,
      pca_components: null,
    });
    const verdict = evaluateWSTResult(lowSnr);
    expect(verdict.action).toBe("SECONDARY_DENOISING");
  });

  test("triggers artifact rejection on high variance outlier", () => {
    const spikyVariance = JSON.stringify({
      snr_db: 15.0,
      variance: [0.01, 0.02, 0.015, 0.01, 0.02, 10000.0],
      null_count: 0,
      n_files_processed: 1,
      output_shape: [2, 6, 16],
      outlier_paths: [5],
      pca_applied: false,
      pca_components: null,
    });
    // Use n_sigma=1.0 so the statistical threshold reliably catches the outlier
    const verdict = evaluateWSTResult(spikyVariance, { variance_n_sigma: 1.0 });
    expect(verdict.action).toBe("ARTIFACT_REJECTION");
    expect(verdict.artifactAnalysis?.hasArtifacts).toBe(true);
  });

  test("uses static threshold when configured", () => {
    const verdict = evaluateWSTResult(goodResult, {
      variance_threshold: 0.005,
    });
    // Several paths exceed 0.005 → artifact rejection
    expect(verdict.action).toBe("ARTIFACT_REJECTION");
    expect(verdict.artifactAnalysis?.strategy).toBe("static");
  });

  test("handles invalid JSON gracefully", () => {
    const verdict = evaluateWSTResult("not valid json");
    expect(verdict.action).toBe("DATA_CORRUPTION_HALT");
    expect(verdict.hasErrors).toBe(true);
  });

  test("handles malformed result schema", () => {
    const verdict = evaluateWSTResult(JSON.stringify({ foo: "bar" }));
    expect(verdict.action).toBe("DATA_CORRUPTION_HALT");
    expect(verdict.hasErrors).toBe(true);
  });
});
