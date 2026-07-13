import Navbar from "@/components/Navbar";
import SiteFooter from "@/components/footer/SiteFooter";
import TierPageShell from "@/components/tiers/TierPageShell";
import PromptRouterStepper from "@/components/tiers/phase-3/PromptRouterStepper";

export const metadata = {
  title: "Phase III — Autonomous Agentic Control · OmniPulse",
  description: "Claude, wired into a real GPU pipeline over stdio. MCP-native control plane.",
};

export default function Phase3Page() {
  return (
    <>
      <Navbar />
      <TierPageShell
        phase="III"
        tierName="Autonomous Agentic Control Tier"
        headline="Claude, wired into a real GPU pipeline over stdio."
        sub="The MCP-native control plane. omnipulse-agent parses operator requests in natural language and routes them to the Rust orchestrator over line-delimited JSON-RPC 2.0 — without ever touching tensor data."
        diagram={<PromptRouterStepper />}
        whatYouGet={[
          "omnipulse-agent on PyPI — the Python control plane (Anthropic SDK + MCPClient + SharedMemoryManager).",
          "Out-of-the-box compatibility with Claude Desktop, Cursor, and any other MCP host.",
          "End-to-end audit trail: every tool call is a JSON line you can replay.",
        ]}
        whatItSolves={[
          "Most 'AI compliance' products bolt an LLM on top of an opaque pipeline. OmniPulse inverts it.",
          "The LLM is a router, not a decision-maker. The deterministic GPU pipeline produces the legally-significant fingerprint.",
        ]}
        pricingNote="Apache 2.0 — free"
        enterpriseUseCases={[
          {
            title: "In-house compliance copilot",
            body: "A single Claude instance that triages incoming media, calls generate_fingerprint, then compare_fingerprints, and surfaces the match probability.",
          },
          {
            title: "Forensic replay",
            body: "Every JSON-RPC frame is appended to a write-once log — the audit story writes itself.",
          },
          {
            title: "MCP-marketplace deployment",
            body: "Publish the toolset to any MCP host and your team gets an agent that cannot fabricate fingerprints because the schema rejects free-form parameters.",
          },
        ]}
        quickstart={`pip install omnipulse-agent omni-wst-core
cargo install omnipulse-mcp
export ANTHROPIC_API_KEY=sk-ant-...
python -m omnipulse_agent.run --wav your.wav`}
        primaryCta={{ label: "↗ View on PyPI", href: "https://pypi.org/project/omnipulse-agent/" }}
        secondaryCta={{ label: "Star omnipulse-agent on GitHub ↗", href: "https://github.com/samvardhan03/omnipulse-agent" }}
      />
      <SiteFooter />
    </>
  );
}
