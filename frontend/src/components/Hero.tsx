import { useState } from 'react';
import { Phone, Play } from 'lucide-react';
import CallbackModal from './CallbackModal';

export default function Hero() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <section className="relative bg-gradient-to-b from-slate-50 to-white pt-20 pb-32 px-6">
        <div className="max-w-6xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-200 rounded-full px-4 py-2 mb-8">
            <Phone className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">Powered by AI</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold text-slate-900 mb-6 tracking-tight leading-tight">
            AI That Makes Phone Calls<br />For Your Business
          </h1>

          <p className="text-xl md:text-2xl text-slate-600 mb-12 max-w-3xl mx-auto leading-relaxed">
            Sounds human. Books appointments. Qualifies leads. Follows up.<br />
            Available 24/7. Never complains. Never takes a sick day.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <button 
              onClick={() => setIsModalOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 rounded-lg text-lg font-semibold transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
            >
              Try it now - FREE
            </button>
            <button 
              onClick={() => setIsModalOpen(true)}
              className="bg-white hover:bg-slate-50 text-slate-900 px-8 py-4 rounded-lg text-lg font-semibold border-2 border-slate-200 transition-all flex items-center gap-2"
            >
              <Play className="w-5 h-5" />
              Hear a sample call
            </button>
          </div>

          <div className="mt-16 flex flex-wrap justify-center gap-8 text-sm text-slate-500">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              No credit card required
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              Setup in 5 minutes
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              Cancel anytime
            </div>
          </div>
        </div>
      </section>

      <CallbackModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </>
  );
}
