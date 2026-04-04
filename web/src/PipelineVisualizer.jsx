import React from 'react';
import { Activity, ShieldCheck, Zap, Database, Combine, BrainCircuit, ArrowDown } from 'lucide-react';

const NodeCard = ({ icon: Icon, title, desc, delay }) => (
  <div className={`relative flex flex-col items-center bg-white border border-slate-200 rounded-2xl p-6 shadow-sm shadow-teal-100 w-full max-w-sm transition-all hover:border-teal-300 hover:shadow-md hover:-translate-y-1 z-10 animate-fade-in-up`} style={{animationDelay: delay}}>
    <div className="h-12 w-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center mb-4 border border-teal-100">
      <Icon size={24} />
    </div>
    <h4 className="text-lg font-bold text-slate-900 text-center mb-2">{title}</h4>
    <p className="text-sm text-slate-600 text-center">{desc}</p>
  </div>
);

const Connector = () => (
  <div className="flex flex-col items-center justify-center py-4 text-indigo-300">
    <div className="w-0.5 h-8 bg-gradient-to-b from-indigo-200 to-indigo-400 rounded-full" />
    <ArrowDown size={24} className="mt-1 flex-shrink-0 animate-bounce" />
  </div>
);

export const PipelineVisualizer = () => {
  return (
    <div className="w-full max-w-4xl mx-auto py-12 px-4 flex flex-col items-center relative">
      <div className="absolute inset-0 bg-gradient-to-b from-slate-50 to-white rounded-[3rem] -z-10 border border-slate-100 shadow-xl shadow-teal-50/50" />
      
      <div className="w-full flex justify-between items-end px-8 mb-8">
         <span className="text-xs font-bold uppercase tracking-widest text-slate-400">TypeScript Orchestrator</span>
         <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Python Engine</span>
      </div>

      <div className="w-full grid grid-cols-1 md:grid-cols-[1fr_80px_1fr] gap-4 md:gap-0 relative">
        
        {/* Left Column (TS Orchestrator) */}
        <div className="flex flex-col items-center space-y-4">
          <NodeCard 
            icon={Activity} 
            title="1. Raw Signal Ingestion" 
            desc="EEG/FRB .npy streams loaded into Orchestrator memory." 
            delay="0ms"
          />
          <Connector />
          <NodeCard 
            icon={ShieldCheck} 
            title="2. Zod Validation" 
            desc="Strict type checking and schema resolution before execution." 
            delay="100ms"
          />
          <Connector />
          <NodeCard 
            icon={Zap} 
            title="3. MCP Bridge Activation" 
            desc="Bun dynamically spawns and bridges the python subprocess via stdio." 
            delay="200ms"
          />
        </div>

        {/* Center Divider / Gap */}
        <div className="hidden md:flex flex-col items-center justify-center relative">
          {/* Horizontal cross connector */}
          <div className="absolute top-[80%] left-1/2 w-full h-0.5 bg-indigo-300 transform -translate-y-1/2 hidden md:block z-0" />
        </div>

        {/* Right Column (Python Engine) */}
        <div className="flex flex-col items-center space-y-4 mt-8 md:mt-24">
          <NodeCard 
            icon={Combine} 
            title="4. Kymatio WST" 
            desc="Cascaded Wavelet Scattering extracts translation-invariant amplitude envelopes." 
            delay="300ms"
          />
          <Connector />
          <NodeCard 
            icon={Database} 
            title="5. PCA Compression" 
            desc="scikit-learn condenses high-variability paths into a K-dimensional manifold." 
            delay="400ms"
          />
          <Connector />
          <NodeCard 
            icon={BrainCircuit} 
            title="6. TF-C Embedding" 
            desc="PyTorch passes reduced tensors through contrastive loss alignment." 
            delay="500ms"
          />
        </div>

      </div>
    </div>
  );
};
