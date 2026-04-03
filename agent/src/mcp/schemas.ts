/**
 * src/mcp/schemas.ts
 * ------------------
 * Zod schemas governing the MCP tool interface between the TypeScript
 * agentic orchestrator and the Python transient_wst MCP server.
 *
 * These schemas enforce strict type-safety at runtime, preventing the
 * LLM QueryEngine from hallucinating invalid wavelet hyperparameters
 * or malformed execution requests.
 */

import { z } from "zod";

// ── ExecuteWST Input Schema ──────────────────────────────────────────────────

/**
 * Validated input for the `execute_wst` MCP tool.
 *
 * Maps 1:1 to the Python MCP server's tool parameters.
 */
export const ExecuteWSTInputSchema = z.object({
  /** Path to directory containing input .npy time-series arrays (shape B×T). */
  input_directory: z
    .string()
    .min(1, "input_directory must be a non-empty path"),

  /** Path to directory where transformed output arrays will be saved. */
  output_directory: z
    .string()
    .min(1, "output_directory must be a non-empty path"),

  /** Signal sampling frequency in Hz. Must be positive. */
  sampling_rate: z
    .number()
    .positive("sampling_rate must be a positive number")
    .default(256.0),

  /**
   * Maximum scattering scale J (power-of-two temporal window).
   * Valid range: 1 ≤ J ≤ 16.
   */
  j_scale: z
    .number()
    .int("j_scale must be an integer")
    .min(1, "j_scale must be ≥ 1")
    .max(16, "j_scale must be ≤ 16"),

  /**
   * Wavelets per octave for the first- and second-order filter banks.
   * Both values must be ≥ 1.
   *
   * Recommended ranges:
   *   - Q1: 8–16 for oscillatory signals (EEG, audio)
   *   - Q2: 1–2 for amplitude modulation capture
   */
  q_wavelets: z.tuple([
    z.number().int().min(1, "Q1 must be ≥ 1"),
    z.number().int().min(1, "Q2 must be ≥ 1"),
  ]),

  /** Whether to apply PCA dimensionality reduction after scattering. */
  apply_pca: z.boolean().default(true),

  /** PCA cumulative variance threshold (0–1). Only used when apply_pca=true. */
  pca_variance: z
    .number()
    .min(0.01, "pca_variance must be > 0")
    .max(1.0, "pca_variance must be ≤ 1.0")
    .default(0.95),
});

export type ExecuteWSTInput = z.infer<typeof ExecuteWSTInputSchema>;

// ── WST Result Schema ────────────────────────────────────────────────────────

/**
 * Parsed JSON result returned by the Python execute_wst MCP tool.
 *
 * This is the structured payload that the QueryEngine evaluates to
 * autonomously decide the next pipeline step.
 */
export const WSTResultSchema = z.object({
  /** Average Signal-to-Noise Ratio in decibels across all processed files. */
  snr_db: z.number(),

  /** Mean per-scattering-path variance vector. */
  variance: z.array(z.number()),

  /** Total count of NaN/Inf values detected across all outputs. */
  null_count: z.number().int().min(0),

  /** Number of input files successfully processed. */
  n_files_processed: z.number().int().min(0),

  /** Shape of the (first) output tensor, e.g. [B, P, T']. */
  output_shape: z.array(z.number().int()),

  /** Indices of scattering paths flagged as statistical outliers. */
  outlier_paths: z.array(z.number().int()),

  /** Whether PCA reduction was applied. */
  pca_applied: z.boolean(),

  /** Number of retained PCA components (null if PCA was not applied). */
  pca_components: z.number().int().nullable(),
});

export type WSTResult = z.infer<typeof WSTResultSchema>;

// ── QueryEngine Evaluation Config ────────────────────────────────────────────

/**
 * Configurable thresholds for the QueryEngine's autonomous evaluation.
 *
 * The variance threshold supports two modes:
 *   1. **Static**: a fixed numeric threshold
 *   2. **Statistical** (default): uses the mean + n_sigma × std_dev approach
 *
 * This is passed dynamically so real-world sensor amplitudes of any
 * domain can be accommodated.
 */
export const EvaluationConfigSchema = z.object({
  /**
   * Static variance threshold. If any path variance exceeds this,
   * the signal is flagged for artifact rejection.
   * Set to `null` to use statistical mode instead.
   */
  variance_threshold: z
    .number()
    .positive()
    .nullable()
    .default(null),

  /**
   * Number of standard deviations above the mean variance to flag
   * as an outlier (statistical mode). Only used when
   * variance_threshold is null.
   */
  variance_n_sigma: z.number().positive().default(3.0),

  /** Minimum acceptable SNR in dB. Below this → recommend denoising. */
  min_snr_db: z.number().default(3.0),

  /** Maximum acceptable null values. Above this → flag corruption. */
  max_null_count: z.number().int().min(0).default(0),
});

export type EvaluationConfig = z.infer<typeof EvaluationConfigSchema>;
