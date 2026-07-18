import Navbar from "@/components/Navbar";
import HeroSection from "@/components/hero/HeroSection";
import ProblemTicker from "@/components/ProblemTicker";
import HeroValueStrip from "@/components/HeroValueStrip";
import TwoLayerMergerSection from "@/components/TwoLayerMergerSection";
import OmniLockEmbedSimulator from "@/components/OmniLockEmbedSimulator";
import TwoLayerSynthIdGrid from "@/components/TwoLayerSynthIdGrid";
import ModularCommercializationGrid from "@/components/grid/ModularCommercializationGrid";
import InteractiveSimulator from "@/components/simulator/InteractiveSimulator";
import EnterprisePricing from "@/components/pricing/EnterprisePricing";
import SisterProductsSection from "@/components/ecosystem/SisterProductsSection";
import FoundersCreatorsBios from "@/components/bios/FoundersCreatorsBios";
import TwoLayerContactSection from "@/components/TwoLayerContactSection";
import FooterCTA from "@/components/footer/FooterCTA";
import SiteFooter from "@/components/footer/SiteFooter";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <ProblemTicker />
        <HeroValueStrip />
        <TwoLayerMergerSection />
        <OmniLockEmbedSimulator />
        <TwoLayerSynthIdGrid />
        <ModularCommercializationGrid />
        <InteractiveSimulator />
        <EnterprisePricing />
        <SisterProductsSection />
        <FoundersCreatorsBios />
        <TwoLayerContactSection />
        <FooterCTA />
      </main>
      <SiteFooter />
    </>
  );
}
