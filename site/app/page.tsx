import Navbar from "@/components/Navbar";
import HeroSection from "@/components/hero/HeroSection";
import ModularCommercializationGrid from "@/components/grid/ModularCommercializationGrid";
import InteractiveSimulator from "@/components/simulator/InteractiveSimulator";
import EnterprisePricing from "@/components/pricing/EnterprisePricing";
import SisterProductsSection from "@/components/ecosystem/SisterProductsSection";
import FoundersCreatorsBios from "@/components/bios/FoundersCreatorsBios";
import FooterCTA from "@/components/footer/FooterCTA";
import SiteFooter from "@/components/footer/SiteFooter";

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        <HeroSection />
        <ModularCommercializationGrid />
        <InteractiveSimulator />
        <EnterprisePricing />
        <SisterProductsSection />
        <FoundersCreatorsBios />
        <FooterCTA />
      </main>
      <SiteFooter />
    </>
  );
}
