import Navbar from "@/components/Navbar";
import SiteFooter from "@/components/footer/SiteFooter";
import TierPageShell from "@/components/tiers/TierPageShell";
import FilterBankExplorer from "@/components/tiers/phase-1/FilterBankExplorer";

export const metadata = {
  title: "Phase I — DSP Primitives · OmniPulse",
  description: "Wavelet scattering, shipped as a wheel. C++/CUDA primitives for audio, vibration, and biosignal pipelines.",
};

export default function Phase1Page() {
  return (
    <>
      <Navbar />
      <TierPageShell
        phase="I"
        tierName="Institutional Research Tier"
        headline="Wavelet scattering, shipped as a wheel."
        sub="Drop-in C++/CUDA primitives for any audio, vibration, or biosignal pipeline that needs translation-invariant, frequency-aware fingerprints. AGPL-3.0 + Commercial."
        diagram={<FilterBankExplorer />}
        whatYouGet={[
          "omni-wst-core PyPI wheel — WSTEngine<HopperTag, J, Q> + analytic Morlet bank + Radix-2 FFT CPU fallback.",
          "JTFS (joint time-frequency scattering) on dual CUDA streams.",
          "15+ GB/s DMA via cudaHostRegister on pinned Plasma pages.",
        ]}
        whatItSolves={[
          "Spectrogram-and-CNN pipelines burn enormous compute to learn what scattering provides analytically.",
          "WST gives you orderable, comparable fingerprints with formal stability guarantees, in milliseconds.",
        ]}
        pricingNote="AGPL-3.0 — free for research & open source"
        enterpriseUseCases={[
          {
            title: "Audio QA / royalty enforcement",
            body: "Detect derivative tracks in a 100M-asset catalogue using deterministic fingerprints.",
          },
          {
            title: "Bioacoustic monitoring",
            body: "Species and event classification on field recordings without retraining for each habitat.",
          },
          {
            title: "Industrial vibration analytics",
            body: "Spot the fault signature in rotating machinery before a model would even converge.",
          },
        ]}
        quickstart={`from omni_wst_core import fingerprint, WSTConfig
fp = fingerprint(signal, WSTConfig(J=8, Q=16, depth=2, jtfs=False))`}
        primaryCta={{ label: "↗ View on PyPI", href: "https://pypi.org/project/omni-wst-core/" }}
        secondaryCta={{ label: "Star omni-wst-core on GitHub ↗", href: "https://github.com/samvardhan03/omni-wst-core" }}
      />
      <SiteFooter />
    </>
  );
}
