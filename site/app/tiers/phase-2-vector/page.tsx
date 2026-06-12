import Navbar from "@/components/Navbar";
import SiteFooter from "@/components/footer/SiteFooter";
import TierPageShell from "@/components/tiers/TierPageShell";
import HnswGraphExplorer from "@/components/tiers/phase-2/HnswGraphExplorer";

export const metadata = {
  title: "Phase II — Vector Substrate · OmniPulse",
  description: "Billion-scale nearest neighbour over distributions, in Rust. Concurrent HNSW + Sliced-Wasserstein.",
};

export default function Phase2Page() {
  return (
    <>
      <Navbar />
      <TierPageShell
        phase="II"
        tierName="High-Velocity Concurrent Processing Tier"
        headline="Billion-scale nearest neighbour over distributions, in Rust."
        sub="Concurrent HNSW with a pluggable distance metric — and the first production-ready Sliced-Wasserstein implementation that composes cleanly with HNSW. AGPL-3.0 + Commercial."
        diagram={<HnswGraphExplorer />}
        whatYouGet={[
          "vector-index — generic ConcurrentHnsw<P, M> over a parking_lot::RwLock-backed index.",
          "sliced-wasserstein — SW₁ over point-cloud fingerprints; implements Metric from vector-index behind a feature flag.",
          "Stable insert/search under high-throughput concurrent ingest.",
        ]}
        whatItSolves={[
          "Cosine and L2 collapse semantically rich fingerprints; SW₁ preserves distributional structure.",
          "HNSW gives you sub-millisecond k-NN. Compose the two for a billion-scale, distributionally-aware index.",
        ]}
        pricingNote="AGPL-3.0 — free for research & open source"
        enterpriseUseCases={[
          {
            title: "Catalogue dedup / matching",
            body: "Stock-audio and stock-video libraries at multi-billion-asset scale.",
          },
          {
            title: "AI-content attribution",
            body: "Find the closest known fingerprint to a freshly generated piece of media.",
          },
          {
            title: "Recommendation over empirical distributions",
            body: "When the 'item' is a behavioural histogram, not a point in space.",
          },
        ]}
        quickstart={`use vector_index::{HnswConfig, concurrent::ConcurrentHnsw};
use sliced_wasserstein::{PointCloud, SlicedWasserstein, SwConfig};

let metric = SlicedWasserstein::new(SwConfig { dim: 172, n_projections: 100, seed: 42 });
let index  = ConcurrentHnsw::new(HnswConfig::default(), metric)?;
index.insert(point_id, PointCloud::new(fp, 172)?)?;
let hits = index.search(&query, 10);`}
        primaryCta={{ label: "↗ View on crates.io", href: "https://crates.io/crates/vector-index" }}
        secondaryCta={{ label: "Star omnipulse-rs on GitHub ↗", href: "https://github.com/samvardhan03/omnipulse-rs" }}
      />
      <SiteFooter />
    </>
  );
}
