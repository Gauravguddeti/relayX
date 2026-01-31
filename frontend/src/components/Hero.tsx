import { useState } from 'react';
import { Phone, Play, Sparkles } from 'lucide-react';
import CallbackModal from './CallbackModal';
import GlassCard from './ui/glass-card';

export default function Hero() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <section className="relative pt-32 pb-40 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-white/60 backdrop-blur-md border border-teal-200/50 rounded-full px-5 py-2.5 mb-8 shadow-lg">
            <Sparkles className="w-4 h-4 text-teal-600 animate-pulse" />
            <span className="text-sm font-semibold bg-gradient-to-r from-cyan-600 to-blue-700 bg-clip-text text-transparent">
              Powered by Advanced AI
            </span>
          </div>

          <h1 className="text-6xl md:text-8xl font-black mb-8 tracking-tight leading-[0.95]">
            <span className="bg-gradient-to-r from-blue-700 via-cyan-600 to-teal-600 bg-clip-text text-transparent">
              AI That Makes
            </span>
            <br />
            <span className="bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
              Phone Calls
            </span>
          </h1>

          <p className="text-xl md:text-2xl text-slate-600 mb-12 max-w-3xl mx-auto leading-relaxed font-medium">
            Sounds human. Books appointments. Qualifies leads.<br />
            <span className="text-teal-600 font-bold">Available 24/7.</span> Never complains. Never takes a sick day.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
            <button 
              onClick={() => setIsModalOpen(true)}
              className="group bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white px-10 py-5 rounded-2xl text-lg font-bold transition-all shadow-2xl hover:shadow-purple-500/50 hover:scale-105 active:scale-95"
            >
              <span className="flex items-center gap-2">
                Try it now - FREE
                <Sparkles className="w-5 h-5 group-hover:rotate-12 transition-transform" />
              </span>
            </button>
            <button 
              onClick={() => setIsModalOpen(true)}
              className="group bg-white/80 backdrop-blur-md hover:bg-white text-slate-900 px-10 py-5 rounded-2xl text-lg font-bold border-2 border-purple-200/50 hover:border-purple-300 transition-all shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 flex items-center gap-3"
            >
              <Play className="w-5 h-5 text-purple-600 group-hover:scale-110 transition-transform" />
              Hear a sample call
            </button>
          </div>

          <GlassCard className="max-w-2xl mx-auto p-8" hover={false}>
            <div className="flex flex-wrap justify-center gap-8 text-sm">
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <div className="w-2.5 h-2.5 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full animate-pulse"></div>
                No credit card required
              </div>
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <div className="w-2.5 h-2.5 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full animate-pulse"></div>
                Setup in 5 minutes
              </div>
              <div className="flex items-center gap-2 text-slate-700 font-medium">
                <div className="w-2.5 h-2.5 bg-gradient-to-r from-green-400 to-emerald-500 rounded-full animate-pulse"></div>
                Cancel anytime
              </div>
            </div>
          </GlassCard>
        </div>
      </section>

      <CallbackModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
}
