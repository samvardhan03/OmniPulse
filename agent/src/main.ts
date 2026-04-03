/**
 * src/main.ts
 * -----------
 * Entry point for the Agentic-Wavelet Orchestrator.
 *
 * Implements the CLI interface for the agent (using Commander), establishing
 * the bridge to the MCP server and invoking the autonomous QueryEngine.
 */

import { Command } from "commander";
import { McpBridge } from "./mcp/McpClient";
import { evaluateWSTResult } from "./query/QueryEngine";
import { executeWST } from "./tools/ExecuteWSTTool";
import * as path from "path";
import * as fs from "fs";

const AGENT_VERSION = "0.1.0";
const AGENT_NAME = "Universal Agentic-Wavelet Orchestrator";

const program = new Command();

program
  .name(AGENT_NAME)
  .description("Terminal-native autonomous MLOps agent")
  .version(AGENT_VERSION);

program
  .command("process")
  .description("Execute End-to-End Dry Run: Kymatio WST, PCA, & Artifact Rejection")
  .requiredOption("--input <dir>", "Input directory containing raw .npy simulation data")
  .requiredOption("--output <dir>", "Output directory for clean, processed tensors")
  .action(async (options) => {
    console.log(`\n▶ Booting ${AGENT_NAME}... (Phase 3 Dry Run)`);
    
    // Convert relative CLI paths to absolute based on execution dir
    const inputDir = path.resolve(process.cwd(), options.input);
    const outputDir = path.resolve(process.cwd(), options.output);

    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // ── 1. Initialize MCP Bridge ──────────────────────────────────────────
    console.log("\n[1] Initializing MCP Bridge...");
    
    // We assume python3 with the active correct virtual environment or that
    // dependencies are available. For robustness during the dry-run, we 
    // construct the absolute patch to the python script if possible, or
    // just rely on the path python3 context. 
    // Usually, the Python module `transient_wst` is installed via pip -e.
    const bridge = new McpBridge({
      // We assume python is accessible. We can point to the virtual environment if needed.
      // But standard `python3` works if run inside the activated venv.
      // Let's use standard.
      pythonCommand: "python3"
    });

    try {
      await bridge.connect();
      console.log("✅ MCP Bridge connected to PyPI backend.");
      
      const tools = await bridge.listTools();
      console.log(`   Discovered Tools: ${tools.map(t => t.name).join(", ")}`);

      // ── 2. The explicit prompt ──────────────────────────────────────────
      console.log("\n[2] Agentic Prompt Submitted:");
      console.log(`
      "Analyze the time-series files in the input directory using the ExecuteWSTTool.
       Evaluate the variance using statistical outliers (mean + 3std).
       If corruption is found, reject those files using ArtifactRejectionTool.
       Save the clean PCA matrices to the output directory."
      `);

      // ── 3. Execute WST ──────────────────────────────────────────────────
      console.log("\n[3] Triggering Wavelet Scattering Transform...");
      
      const result = await executeWST(bridge, {
        input_directory: inputDir,
        output_directory: outputDir,
        sampling_rate: 1000.0,
        j_scale: 8,
        q_wavelets: [8, 1], // Oscillatory configuration
        apply_pca: true,
        pca_variance: 0.95
      });

      if (!result.success || !result.data) {
        console.error("❌ ExecuteWSTTool failed:", result.error);
        process.exit(1);
      }
      
      // ── 4. Query Engine Evaluation ──────────────────────────────────────
      console.log("\n[4] Booting QueryEngine Evaluation...");
      const rawJson = JSON.stringify(result.data); // simulate raw json parsing
      
      // We pass the explicit requirement of mean + 3std down
      const verdict = evaluateWSTResult(rawJson, {
        variance_n_sigma: 3.0
      });

      console.log("\n====== PIPELINE VERDICT ======");
      console.log(`Decision : ${verdict.action}`);
      console.log(`Reasoning: ${verdict.reasoning}`);
      
      if (verdict.artifactAnalysis && verdict.artifactAnalysis.hasArtifacts) {
        console.log(`Flagged Artifact Paths: ${verdict.artifactAnalysis.flaggedPaths.join(", ")}`);
      }
      
      if (verdict.hasErrors) {
        console.error(`Errors   : ${verdict.error}`);
      }
      console.log("==============================\n");

    } catch (e) {
      console.error("\n❌ Orchestrator encountered a fatal error:", e);
    } finally {
      await bridge.disconnect();
    }
  });

program.parse(Bun.argv);