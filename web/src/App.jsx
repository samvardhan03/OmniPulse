import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';
import { BrainCircuit, Activity, Shrink, Zap, ShieldAlert, Cpu } from 'lucide-react';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: true,
  theme: 'dark',
  themeVariables: {
    fontFamily: 'Inter, sans-serif',
    primaryColor: '#3B82F6',
    primaryTextColor: '#fff',
    primaryBorderColor: '#1E293B',
    lineColor: '#8B5CF6',
    secondaryColor: '#10B981',
    tertiaryColor: '#1E293B',
  }
});

const MermaidDiagram = ({ chart }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      mermaid.render(`mermaid-${Math.random().toString(36).substr(2, 9)}`, chart).then((result) => {
        ref.current.innerHTML = result.svg;
      });
    }
  }, [chart]);

  return <div ref={ref} className="flex justify-center my-8 p-4 glass rounded-2xl" />;
};

const FeatureCard = ({ icon: Icon, title, description }) => (
  <div className="glass-card">
    <div className="h-12 w-12 rounded-full bg-primary/20 flex items-center justify-center mb-6 border border-primary/30 text-primary">
      <Icon size={24} />
    </div>
    <h3 className="text-xl font-outfit font-semibold mb-3 text-white">{title}</h3>
    <p className="text-slate-400 leading-relaxed font-inter">{description}</p>
  </div>
);

function App() {
  const architectureChart = `
    flowchart TD
      A[Noisy Signal<br>EEG / FRB] -->|Continuous input| B(Agentic Query Engine)
      subgraph Python Scientific Engine
        C[Wavelet Scattering<br>Transform] -->|Kymatio S0, S1, S2| D[PCA Compression]
      end
      B -->|MCP Execution| C
      D -->|K-dimensional Manifold| E{Artifact Rejection Tool}
      E -->|Statistical Threshold<br>Mean + 3σ| F[Clean Tensor]
      E -->|Anomaly Detected| G[Flagged for Denoising]
      F --> H(((Foundation<br>Tokenization)))
  `;

  return (
    <div className="min-h-screen selection:bg-primary/30">
      {/* Navigation */}
      <nav className="fixed w-full z-50 glass border-b-0 border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-gradient-to-tr from-primary to-accent rounded-xl flex items-center justify-center shadow-lg shadow-primary/20">
              <Activity className="text-white" size={20} />
            </div>
            <span className="font-outfit font-bold text-xl tracking-wide text-white">AgenticWavelet</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-300">
            <a href="#features" className="hover:text-primary transition-colors">Architecture</a>
            <a href="#pipeline" className="hover:text-primary transition-colors">Pipeline</a>
            <a href="#mcp" className="hover:text-primary transition-colors">MCP Protocol</a>
            <button className="bg-white/10 hover:bg-white/20 text-white px-5 py-2.5 rounded-full transition-all border border-white/10 hover:border-white/30">
              View on GitHub
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-40 pb-20 px-6 relative overflow-hidden">
        {/* Abstract Background Elements */}
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-primary/20 rounded-full blur-[120px] -z-10 mix-blend-screen animate-pulse" />
        <div className="absolute top-1/3 right-1/4 w-[400px] h-[400px] bg-accent/20 rounded-full blur-[100px] -z-10 mix-blend-screen" />
        
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/30 bg-primary/10 text-primary text-sm font-medium mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            Phase 3 Engine Dry-Run Active
          </div>
          <h1 className="text-5xl md:text-7xl font-outfit font-extrabold tracking-tight mb-8">
            Universal Transient <br/>
            <span className="text-gradient">Detection Pipeline.</span>
          </h1>
          <p className="text-lg md:text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed">
            Domain-agnostic Agentic MLOps for high-noise time-series data. 
            Transform raw signals into pristine tokens using Wavelet Scattering Transforms and autonomous MCP evaluation.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button className="h-14 px-8 rounded-full bg-gradient-to-r from-primary to-accent text-white font-semibold flex items-center gap-2 shadow-lg shadow-primary/25 hover:shadow-primary/40 hover:-translate-y-0.5 transition-all w-full sm:w-auto justify-center">
              Execute Dry Run <Cpu size={18} />
            </button>
            <button className="h-14 px-8 rounded-full bg-surface border border-white/10 text-white font-semibold flex items-center gap-2 hover:bg-white/5 transition-all w-full sm:w-auto justify-center">
              Read Documentation
            </button>
          </div>
        </div>
      </section>

      {/* Visual Diagram Section */}
      <section id="pipeline" className="py-24 px-6 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-outfit font-bold mb-4">Pipeline Architecture</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              A fully autonomous orchestrator bridges a TypeScript Model Context Protocol client with a PyTorch scientific engine.
            </p>
          </div>
          <MermaidDiagram chart={architectureChart} />
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="py-24 px-6 relative z-10 bg-black/20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-outfit font-bold mb-4">Core Capabilities</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Mathematical rigor meets intelligent agentic orchestration.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <FeatureCard 
              icon={Activity}
              title="Kymatio WST"
              description="Cascaded Wavelet Scattering Transforms extracting non-stationary transients (S0, S1, S2) from high-noise data."
            />
            <FeatureCard 
              icon={Shrink}
              title="PCA Dimensionality Reduction"
              description="Compression of the multi-path representation into a compact K-dimensional manifold retaining 95% variance."
            />
            <FeatureCard 
              icon={BrainCircuit}
              title="Agentic Query Engine"
              description="LLM-driven evaluation loops autonomously orchestrating data transformations and dynamically passing JSON commands."
            />
            <FeatureCard 
              icon={ShieldAlert}
              title="Artifact Rejection Tool"
              description="Dual-mode anomaly detection. Uses 'mean + 3σ' statistical outliers to flag corrupted channels autonomously."
            />
            <FeatureCard 
              icon={Zap}
              title="Model Context Protocol"
              description="Type-safe bridging between the Bun/TypeScript orchestrator and the Python FastMCP PyPI native backend."
            />
            <FeatureCard 
              icon={Cpu}
              title="Foundation TF-C Stub"
              description="PyTorch contrastive loss alignment projecting time-series data into unified embeddings."
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 mt-20 py-12 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4 text-slate-500 text-sm">
          <div className="flex items-center gap-2">
             <Activity size={16} className="text-primary" />
             <span>Agentic Wavelet Foundation Pipeline — Phase 3</span>
          </div>
          <p>Powered by Bun, Vite & Kymatio</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
