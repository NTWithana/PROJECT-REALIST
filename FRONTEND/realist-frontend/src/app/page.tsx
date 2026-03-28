import Hero from "@/components/ui/Hero";
import HowItWorks from "@/components/ui/HowItWorks";
import CoEvolution from "@/components/ui/CoEvolution";
import WhyDifferent from "@/components/ui/WhyDifferent";
import Footer from "@/components/ui/Footer";

export default function Home() {
  return (
    <main>
      <Hero />
      <CoEvolution />
      <WhyDifferent />
      <HowItWorks />
      <Footer />
    </main>
  );
}
