import Navbar from "@/components/Navbar";
import SiteFooter from "@/components/footer/SiteFooter";
import TierPageShell from "@/components/tiers/TierPageShell";
import AutoscalerSimulator from "@/components/tiers/enterprise/AutoscalerSimulator";

export const metadata = {
  title: "Enterprise: SaaS Pipeline · OmniPulse",
  description: "Multi-tenant, autoscaled, audit-ready. The complete cloud-native deployment.",
};

export default function EnterprisePage() {
  return (
    <>
      <Navbar />
      <TierPageShell
        phase="ENTERPRISE"
        tierName="Cloud-Native Deployment"
        headline="Multi-tenant, autoscaled, audit-ready."
        sub="The complete cloud-native deployment of the four-module stack. Kubernetes control plane, GPU autoscaling driven by Prometheus queue depth, ed25519-signed license tokens, IPFS pinning."
        diagram={<AutoscalerSimulator />}
        whatYouGet={[
          "Helm chart, Terraform module, and a managed Anthropic key tier.",
          "HSM-backed ed25519 signing keys for license token issuance.",
          "SOC 2 + ISO 27001 roadmap (committed dates available under NDA).",
          "24/7 enterprise SLA, dedicated solutions engineer.",
        ]}
        whatItSolves={[
          "Self-hosting the four-module stack requires GPU ops, MCP plumbing, key management, and IPFS infra.",
          "Enterprise collapses that into a single contract.",
        ]}
        pricingNote="Contract pricing"
        enterpriseUseCases={[
          {
            title: "Major label / studio",
            body: "Ingest every release into a private fingerprint catalogue with audit-grade attestations.",
          },
          {
            title: "Generative-platform compliance officer",
            body: "Prove that every generation either has provenance or has paid a licensable origin.",
          },
          {
            title: "Regulators / industry watchdogs",
            body: "Standing query API over public fingerprint catalogues.",
          },
        ]}
        quickstart=""
        primaryCta={{ label: "Talk to founders →", href: "mailto:shekhawatsamvardhan@gmail.com" }}
      />
      <SiteFooter />
    </>
  );
}
