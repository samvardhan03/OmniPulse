import React from 'react';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';
import { BrainCircuit, Activity, Shrink, Zap, ShieldAlert, Cpu, Github, Package, CheckCircle2, Factory, Mail, Radio, Brain } from 'lucide-react';
import { PipelineVisualizer } from './PipelineVisualizer';

const FeatureCard = ({ icon: Icon, title, description }) => (
  <div className="bg-white border border-slate-200 rounded-2xl p-8 transition-all duration-300 hover:border-teal-300 hover:-translate-y-1 hover:shadow-xl hover:shadow-teal-100/50">
    <div className="h-14 w-14 rounded-2xl bg-teal-50 flex items-center justify-center mb-6 border border-teal-100 text-teal-600 shadow-sm shadow-teal-50">
      <Icon size={26} strokeWidth={2} />
    </div>
    <h3 className="text-xl font-bold mb-3 text-slate-900">{title}</h3>
    <p className="text-slate-600 leading-relaxed font-medium">{description}</p>
  </div>
);

const AppCard = ({ icon: Icon, title, description }) => (
  <div className="bg-white border border-indigo-100 rounded-2xl p-6 shadow-md shadow-indigo-50/50 flex flex-col transition-all hover:shadow-lg hover:-translate-y-1 hover:border-indigo-300">
    <div className="flex items-center gap-4 mb-4">
      <div className="h-12 w-12 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600">
        <Icon size={24} />
      </div>
      <h3 className="text-lg font-bold text-slate-900 leading-tight">{title}</h3>
    </div>
    <p className="text-slate-600 font-medium leading-relaxed flex-grow">{description}</p>
  </div>
);

function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 selection:bg-teal-100 selection:text-teal-900 font-sans">
      {/* Navigation */}
      <nav className="fixed w-full z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-gradient-to-tr from-teal-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-md shadow-teal-200">
              <Activity className="text-white" size={20} />
            </div>
            <span className="font-bold text-2xl tracking-tight text-slate-900">OmniPulse</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-bold text-slate-600">
            <a href="#pipeline" className="hover:text-teal-600 transition-colors">Architecture</a>
            <a href="#mechanics" className="hover:text-teal-600 transition-colors">Mechanics</a>
            <a href="#applications" className="hover:text-teal-600 transition-colors">Applications</a>
            <a href="#enterprise" className="hover:text-teal-600 transition-colors">Integration</a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-40 pb-24 px-6 relative overflow-hidden flex flex-col items-center bg-gradient-to-b from-white to-slate-50 border-b border-slate-200">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-teal-200 bg-teal-50 text-teal-700 text-sm font-bold mb-8 shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
            </span>
            v0.1.0 Released on PyPI
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 text-slate-900">
            Domain-Agnostic <br/>
            <span className="bg-clip-text text-transparent bg-gradient-to-r from-teal-600 to-indigo-600">Signal Intelligence.</span>
          </h1>
          <p className="text-lg md:text-xl text-slate-700 mb-12 max-w-2xl mx-auto leading-relaxed font-medium">
            Agentic Model Context Protocol (MCP) for Universal Transient Signal Processing. OmniPulse brings translation-invariant mathematical rigor to extreme high-noise arrays.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <a href="https://github.com/samvardhan03/OmniPulse" target="_blank" rel="noreferrer" className="h-14 px-8 rounded-full bg-slate-900 text-white font-bold flex items-center gap-2 shadow-lg shadow-slate-200 hover:shadow-slate-300 hover:-translate-y-0.5 transition-all w-full sm:w-auto justify-center">
              View on GitHub <Github size={18} />
            </a>
            <a href="https://pypi.org/project/omnipulse/" target="_blank" rel="noreferrer" className="h-14 px-8 rounded-full bg-white border-2 border-slate-200 text-teal-600 font-bold flex items-center gap-2 hover:bg-slate-50 hover:border-teal-200 shadow-sm transition-all w-full sm:w-auto justify-center">
              View on PyPI <Package size={18} />
            </a>
          </div>
        </div>
      </section>

      {/* Visual Diagram Section */}
      <section id="pipeline" className="py-24 px-6 relative z-10 bg-slate-50">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4 text-slate-900">The Decoupled Architecture</h2>
            <p className="text-slate-600 max-w-2xl mx-auto text-lg font-medium">
              TypeScript orchestrates the heuristics. PyTorch and Kymatio handle the wavelets.
            </p>
          </div>
          <PipelineVisualizer />
        </div>
      </section>

      {/* Mechanics: Rigorous Signal Decomposition */}
      <section id="mechanics" className="py-24 px-6 bg-gradient-to-r from-teal-50 to-indigo-50 border-y border-slate-200 relative overflow-hidden">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-teal-200 bg-white text-teal-700 text-xs font-bold mb-6 tracking-wider uppercase">
              Mathematical Rigor
            </div>
            <h2 className="text-3xl md:text-4xl font-extrabold mb-6 text-slate-900">Rigorous Signal Decomposition</h2>
            <p className="text-lg text-slate-700 font-medium leading-relaxed mb-6">
              Fourier constraints fail on non-stationary transients due to a lack of temporal localization. OmniPulse leverages the Kymatio backend to execute cascaded <strong>Wavelet Scattering Transforms (WST)</strong>, yielding translation-invariant amplitude envelopes.
            </p>
            <p className="text-lg text-slate-700 font-medium leading-relaxed">
              By passing extreme-noise data streams through deep, non-linear convolutional filter banks, we expose structural harmonics hidden beneath dense instrumental glitches.
            </p>
          </div>
          
          <div className="bg-slate-800 rounded-3xl p-8 shadow-2xl shadow-indigo-900/20 font-mono text-sm shadow-inner relative overflow-hidden">
             {/* Terminal dots */}
             <div className="flex gap-2 mb-6 opacity-30">
               <div className="w-3 h-3 rounded-full bg-red-400"></div>
               <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
               <div className="w-3 h-3 rounded-full bg-green-400"></div>
             </div>
             
             <div className="space-y-6">
               <div>
                  <span className="text-slate-400 text-xs uppercase tracking-widest font-bold">Zeroth Order (Averaging)</span>
                  <div className="text-teal-400 mt-2 bg-slate-900/50 p-4 rounded-xl border border-teal-900/30">
                    <BlockMath math="S_0x = x * \phi" />
                  </div>
               </div>
               <div>
                  <span className="text-slate-400 text-xs uppercase tracking-widest font-bold">First Order (Scalogram)</span>
                  <div className="text-teal-400 mt-2 bg-slate-900/50 p-4 rounded-xl border border-teal-900/30 overflow-x-auto">
                    <BlockMath math="S_1x(t,\lambda) = |x * \psi_\lambda| * \phi(t)" />
                  </div>
               </div>
               <div>
                  <span className="text-slate-400 text-xs uppercase tracking-widest font-bold">Second Order (Non-linear Modulation)</span>
                  <div className="text-teal-400 mt-2 bg-slate-900/50 p-4 rounded-xl border border-teal-900/30 overflow-x-auto">
                    <BlockMath math="S_2x(t,\lambda_1,\lambda_2) = ||x * \psi_{\lambda_1}| * \psi_{\lambda_2}| * \phi(t)" />
                  </div>
               </div>
             </div>
          </div>
        </div>
      </section>

      {/* Cross-Disciplinary Applications */}
      <section id="applications" className="py-24 px-6 bg-white shrink">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4 text-slate-900">Cross-Disciplinary Extensibility</h2>
            <p className="text-slate-600 max-w-2xl mx-auto text-lg font-medium">
              A domain-agnostic orchestrator capable of mapping anomalies across fundamentally different scientific pipelines.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-6">
            <AppCard 
              icon={Radio}
              title="Radio Astronomy"
              description="Detecting Fast Radio Bursts (FRBs) by isolating distinct dispersion measures and scattering tails directly from non-Gaussian RFI interference."
            />
            <AppCard 
              icon={Activity}
              title="Gravitational Waves"
              description="Extracting complex compact-object merger chirps (binary black holes) otherwise completely buried in instrumental laser glitches."
            />
            <AppCard 
              icon={Brain}
              title="Neurology & EEG"
              description="Isolating non-stationary epileptic spikes, emotional arousal states, and neural oscillations out from biological noise floors."
            />
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 px-6 relative z-10 bg-slate-50 border-t border-slate-200">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4 text-slate-900">Core Engine Capabilities</h2>
            <p className="text-slate-600 max-w-2xl mx-auto text-lg font-medium">
              Enterprise-grade signal decomposition mapped natively to autonomous workflows.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <FeatureCard 
              icon={Activity}
              title="Kymatio WST"
              description="Cascaded Wavelet Scattering Transforms extracting non-stationary transients from extreme high-noise environments."
            />
            <FeatureCard 
              icon={Shrink}
              title="Manifold Compression"
              description="Algorithmic dimensionality reduction to a compact K-dimensional plane retaining 95% of statistical variance."
            />
            <FeatureCard 
              icon={BrainCircuit}
              title="Agentic Orchestrator"
              description="Dynamic TS-powered LLM loops managing mathematical transformations and JSON schema payload parsing."
            />
            <FeatureCard 
              icon={ShieldAlert}
              title="Anomaly Thresholds"
              description="Dual-mode rejection utilizing rigorous 'mean + 3σ' statistical gating to autonomously flag corruption streams."
            />
            <FeatureCard 
              icon={Zap}
              title="MCP Tool Linking"
              description="Type-safe bridging isolating Node.js process state from the underlying Python mathematical engine."
            />
            <FeatureCard 
              icon={Cpu}
              title="Foundation Extensibility"
              description="Ready for PyTorch contrastive alignments. Easily project temporal data arrays into generalized transformer spaces."
            />
          </div>
        </div>
      </section>

      {/* Enterprise Consulting */}
      <section id="enterprise" className="py-24 px-6 bg-white border-t border-slate-200 relative overflow-hidden">
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-extrabold mb-4 text-slate-900">Integration Tiers</h2>
            <p className="text-slate-600 max-w-2xl mx-auto text-lg font-medium">
              Flexible deployments for independent researchers or massive industrial clusters.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto items-stretch">
            {/* Free Tier */}
            <div className="bg-slate-50 border-2 border-slate-200 rounded-3xl p-10 flex flex-col shadow-sm">
              <h3 className="text-2xl font-bold mb-2 text-slate-900">Community (Apache 2.0)</h3>
              <p className="text-slate-600 mb-8 font-medium">For researchers and independent developers.</p>
              <div className="text-5xl font-extrabold mb-8 text-slate-900">$0<span className="text-xl text-slate-500 font-bold">/forever</span></div>
              <ul className="space-y-5 mb-10 flex-grow">
                <li className="flex items-center gap-3 text-slate-700 font-medium"><CheckCircle2 className="text-teal-600" size={24}/> Core Python Engine (PyPI)</li>
                <li className="flex items-center gap-3 text-slate-700 font-medium"><CheckCircle2 className="text-teal-600" size={24}/> TypeScript Orchestrator Agent</li>
                <li className="flex items-center gap-3 text-slate-700 font-medium"><CheckCircle2 className="text-teal-600" size={24}/> Standard MCP Documentation</li>
                <li className="flex items-center gap-3 text-slate-700 font-medium"><CheckCircle2 className="text-teal-600" size={24}/> GitHub Community Support</li>
              </ul>
            </div>

            {/* Pro Tier */}
            <div className="bg-white border-2 border-indigo-600 rounded-3xl p-10 flex flex-col relative shadow-xl shadow-indigo-100/50">
              <div className="absolute top-0 right-0 bg-indigo-600 text-white text-xs font-bold px-4 py-1.5 rounded-bl-xl rounded-tr-3xl uppercase tracking-wider">
                Lab / Enterprise
              </div>
              <h3 className="text-2xl font-bold mb-2 text-slate-900">Lab & Enterprise Integration</h3>
              <p className="text-slate-600 mb-8 font-medium">For Exascale astrophysics and clinical deployments.</p>
              <div className="text-5xl font-extrabold mb-8 text-indigo-600">Custom</div>
              <ul className="space-y-5 mb-10 flex-grow">
                <li className="flex items-center gap-3 text-slate-900 font-bold"><Factory className="text-indigo-600" size={24}/> Proprietary Data Ingestion Pipelines</li>
                <li className="flex items-center gap-3 text-slate-900 font-bold"><BrainCircuit className="text-indigo-600" size={24}/> Custom Quantum Kernel Integrations</li>
                <li className="flex items-center gap-3 text-slate-900 font-bold"><Cpu className="text-indigo-600" size={24}/> Exascale Multi-Node Orchestration</li>
                <li className="flex items-center gap-3 text-slate-900 font-bold"><ShieldAlert className="text-indigo-600" size={24}/> SLA & Dedicated Support</li>
              </ul>
              <a href="mailto:shekhawatsamvardhan@gmail.com" className="w-full h-14 bg-indigo-600 text-white rounded-full font-bold flex items-center justify-center gap-2 hover:bg-indigo-700 transition-colors shadow-md">
                <Mail size={18}/> Contact for Implementation
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-50 border-t border-slate-200 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row text-center justify-between items-center gap-4 text-slate-600 text-sm font-medium">
          <div className="flex items-center gap-2 justify-center">
             <Activity size={18} className="text-teal-600" />
             <span className="font-bold text-slate-900 text-lg">OmniPulse</span>
          </div>
          <p>&copy; 2026 Samvardhan Singh. Released under the Apache 2.0 License.</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
