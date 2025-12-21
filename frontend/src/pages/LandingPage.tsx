import LandingNav from '../components/LandingNav';
import Hero from '../components/Hero';
import Features from '../components/Features';
import DemoRecordings from '../components/DemoRecordings';
import PainSolution from '../components/PainSolution';
import FeatureGrid from '../components/FeatureGrid';
import Pricing from '../components/Pricing';
import Testimonials from '../components/Testimonials';
import FinalCTA from '../components/FinalCTA';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      <LandingNav />
      <div className="pt-16">
        <Hero />
        <Features />
        <DemoRecordings />
        <PainSolution />
        <FeatureGrid />
        <Pricing />
        <Testimonials />
        <FinalCTA />
      </div>
    </div>
  );
}
