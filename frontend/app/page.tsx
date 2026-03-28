'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AlertCircle, PieChart, Route, FileCheck, Target, SearchCheck, 
  Calendar, RefreshCw, Box, Store, Users, Activity, Lock, 
  HeartPulse, ShieldCheck, Gavel, Settings, ShieldAlert, 
  BarChart3, TrendingUp, Factory, Lightbulb 
} from 'lucide-react';

import InputPanel from '@/components/InputPanel';
import AgentPipeline from '@/components/AgentPipeline';
import AgentLog from '@/components/AgentLog';
import BRDOutput from '@/components/BRDOutput';
import Analytics from '@/components/Analytics';
import Timeline from '@/components/Timeline';
import Priorities from '@/components/Priorities';
import SourceTrace from '@/components/SourceTrace';
import ExportBRDButton from '@/components/ExportBRDButton';
import SuggestionsPanel from '@/components/SuggestionsPanel';
import FaissStatsBadge from '@/components/FaissStatsBadge';

import { BRDState, PipelineStep, ExtractionEvent, ModelStats } from '@/lib/types';
import { extractBRD, getHealth, getModelStats } from '@/lib/api';
import { initialPipeline, domainPipelines } from '@/lib/samples';
import { cn } from '@/lib/utils';
import { SelectedReqProvider } from '@/context/SelectedReqContext';

export default function Home() {
  const [state, setState] = useState<BRDState>({
    functional: [],
    nfr: [],
    stakeholders: [],
    decisions: [],
    timeline: [],
    scope: { inScope: [], outOfScope: [] },
    gaps: [],
    priorities: [],
    analytics: null,
    pipeline: initialPipeline,
    domain: 'software',
    domain_data: null,
    logs: [],
    isExtracting: false,
    error: null,
    summary_labels: {
      card1: 'Functional',
      card2: 'Non-Functional',
      card3: 'Stakeholders',
      card4: 'Decisions'
    }
  });

  const [backendOffline, setBackendOffline] = useState(false);
  const [currentSourceText, setCurrentSourceText] = useState('');
  const [activeTab, setActiveTab] = useState('brd');
  const [modelStats, setModelStats] = useState<ModelStats[]>([]);
  const [generationCount, setGenerationCount] = useState(0);
  const [isMounted, setIsMounted] = useState(false);

  // Domain-specific UI themes for high-impact visual feedback
  const domainThemes: Record<string, { accent: string, text: string, ring: string, hover: string, bg: string, border: string }> = {
    software: { 
      accent: 'bg-indigo-600', 
      text: 'text-indigo-600', 
      ring: 'ring-indigo-600/10', 
      hover: 'hover:border-indigo-200/60', 
      bg: 'bg-indigo-50/50',
      border: 'border-indigo-100/50'
    },
    healthcare: { 
      accent: 'bg-emerald-600', 
      text: 'text-emerald-600', 
      ring: 'ring-emerald-600/10', 
      hover: 'hover:border-emerald-200/60', 
      bg: 'bg-emerald-50/50',
      border: 'border-emerald-100/50'
    },
    mechanical: { 
      accent: 'bg-amber-600', 
      text: 'text-amber-600', 
      ring: 'ring-amber-600/10', 
      hover: 'hover:border-amber-200/60', 
      bg: 'bg-amber-50/50',
      border: 'border-amber-100/50'
    },
    business: { 
      accent: 'bg-slate-700', 
      text: 'text-slate-700', 
      ring: 'ring-slate-700/10', 
      hover: 'hover:border-slate-300/60', 
      bg: 'bg-slate-50/50',
      border: 'border-slate-200/50'
    },
  };

  const theme = domainThemes[state.domain || 'software'] || domainThemes.software;

  useEffect(() => {
    setIsMounted(true);
    const checkHealth = async () => {
      const health = await getHealth();
      setBackendOffline(health.status === 'offline');
    };
    checkHealth();
  }, []);

  useEffect(() => {
    if (activeTab === 'analytics') {
      getModelStats().then(setModelStats);
    }
  }, [activeTab]);

  const getCardIcon = (cardIndex: number) => {
    const d = state.domain || 'software';
    const icons: Record<string, any[]> = {
      software: [Box, Store, Users, Target],
      healthcare: [HeartPulse, ShieldCheck, Users, Gavel],
      mechanical: [Settings, ShieldAlert, Users, Factory],
      business: [BarChart3, TrendingUp, Users, Gavel]
    };
    const IconList = icons[d] || icons.software;
    const Icon = IconList[cardIndex];
    return <Icon className="w-[18px] h-[18px]" />;
  };

  const handleExtract = useCallback(async (text: string, domain: BRDState['domain'] = 'software', sourceType: string = 'document') => {
    setCurrentSourceText(text);
    setState(prev => ({
      ...prev,
      isExtracting: true,
      domain,
      error: null,
      logs: [`[${new Date().toLocaleTimeString()}] [system] Starting ${domain} extraction...`],
      pipeline: (domainPipelines[domain as keyof typeof domainPipelines] || initialPipeline).map(s => ({ ...s, status: 'idle' as const }))
    }));

    await extractBRD({
      text,
      sourceType: sourceType as 'email' | 'meeting' | 'chat' | 'document',
      domain,
      onEvent: (event: ExtractionEvent) => {
        const { type, payload } = event;
        setState(prev => {
          let newState = { ...prev };
          const timestamp = new Date().toLocaleTimeString();

          if (type === 'log') {
            newState.logs = [...prev.logs, `[${timestamp}] ${payload}`];
          } else if (type === 'node_complete') {
            const { id, status } = payload as { id: PipelineStep['id'], status: PipelineStep['status'] };
            newState.pipeline = prev.pipeline.map(step =>
              step.id === id ? { ...step, status, timestamp } : step
            );
          } else if (type === 'error') {
            newState.isExtracting = false;
            newState.error = payload as string;
            newState.logs = [...newState.logs, `[${timestamp}] [error] ${payload}`];
          }
          return newState;
        });
      },
      onError: (err: string) => {
        setState(prev => ({
          ...prev,
          isExtracting: false,
          error: err,
          logs: [...prev.logs, `[${new Date().toLocaleTimeString()}] [error] ${err}`]
        }));
      },
      onDone: (finalState: any) => {
        setGenerationCount(prev => prev + 1);
        setState(prev => ({
          ...prev,
          ...finalState,
          isExtracting: false,
          pipeline: prev.pipeline.map(s => ({ ...s, status: 'done' })),
          logs: [...prev.logs, `[${new Date().toLocaleTimeString()}] [system] Extraction finalized.`]
        }));
      }
    });
  }, []);

  const handleCardClick = (tabId: string, sectionId?: string) => {
    setActiveTab(tabId);
    if (sectionId) {
      setTimeout(() => {
        const el = document.getElementById(sectionId);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    }
  };

  return (
    <SelectedReqProvider>
      <div className={cn("flex h-screen bg-[#FBFBFA] font-sans antialiased text-[#37352F] overflow-hidden", state.isExtracting && "animate-pulse-subtle")}>
        {/* Sidebar */}
        <aside className="w-[240px] bg-[#F7F7F5] flex flex-col justify-between h-full py-6 border-r border-[#E5E7EB] z-10 shrink-0">
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="px-5 flex items-center gap-2.5 mb-8 shrink-0">
              <div className={cn("w-6 h-6 rounded flex items-center justify-center text-white font-semibold text-sm transition-colors", theme.accent)}>
                {state.domain === 'software' ? 'A' : state.domain === 'healthcare' ? 'H' : state.domain === 'mechanical' ? 'M' : 'B'}
              </div>
              <span className="text-base font-semibold tracking-tight text-[#37352F]">ApexBRD+</span>
              <div className="ml-auto">
                <div className={cn("text-[10px] font-medium px-1.5 py-0.5 rounded uppercase tracking-wide ring-1 ring-inset transition-colors", theme.bg, theme.text, theme.ring)}>
                  {state.domain}
                </div>
              </div>
            </div>

            <div className="px-3 shrink-0">
              <p className="px-3 text-[10px] font-bold text-gray-400 mb-2 uppercase tracking-[0.1em] leading-relaxed opacity-60">Views</p>
              <nav className="space-y-0.5">
                {[
                  { id: 'brd', label: 'Document', icon: FileCheck },
                  { id: 'analytics', label: 'Analytics', icon: PieChart },
                  { id: 'timeline', label: 'Roadmap', icon: Route },
                  { id: 'priorities', label: 'Strategy', icon: Target },
                  { id: 'trace', label: 'Source Trace', icon: SearchCheck },
                  { id: 'suggestions', label: 'AI Suggestions', icon: Lightbulb },
                ].map((item) => (
                  <button 
                    key={item.id}
                    onClick={() => setActiveTab(item.id)} 
                    className={cn(
                      "w-full flex items-center gap-2.5 px-3 py-1.5 text-[13px] rounded-md transition-all duration-150", 
                      activeTab === item.id 
                        ? `${theme.bg} ${theme.text} font-medium shadow-[0_1px_2px_rgba(0,0,0,0.05)]` 
                        : "text-gray-600 hover:bg-[#EAEAEA] font-normal"
                    )}
                  >
                    <item.icon className={cn("w-4 h-4", activeTab === item.id ? theme.text : "text-gray-400")} /> 
                    {item.label}
                  </button>
                ))}
              </nav>
            </div>

            <div className="px-3 mt-8 flex-1 overflow-y-auto min-h-0 border-t border-gray-200/40 pt-6 mx-2 pb-4 scrollbar-notion">
              <p className="px-3 text-[10px] font-bold text-gray-400 mb-2 uppercase tracking-[0.1em] leading-relaxed opacity-60">Pipeline Status</p>
              <div className="px-2 mt-2">
                <AgentPipeline steps={state.pipeline} />
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden px-10 py-8 bg-white">
          {/* Health Banner */}
          {backendOffline && (
            <div className="bg-red-50/50 border border-red-100 p-2 rounded-lg mb-6 flex items-center justify-center gap-2 text-[11px] font-semibold text-red-600 transition-all">
              <AlertCircle className="w-3.5 h-3.5" />
              BACKEND OFFLINE (http://localhost:8000)
            </div>
          )}

          {/* Header */}
          <header className="flex justify-between items-center mb-10 shrink-0">
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-semibold text-gray-900 tracking-tight">Requirement Extraction</h1>
            </div>
            <div className="flex items-center gap-4">
              <FaissStatsBadge refreshTrigger={generationCount} />
              <ExportBRDButton data={state} />
              <div className="flex items-center gap-2.5 text-[13px] font-medium text-gray-500 bg-gray-50/50 px-4 py-2 rounded-lg border border-gray-100/80">
                <Calendar className="w-3.5 h-3.5 text-gray-400" /> {isMounted ? new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }) : 'Loading Date...'}
              </div>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto pb-20 scrollbar-notion pr-4">
            <div className="flex gap-8">
              <div className="flex-1 flex flex-col min-w-0">
                {/* 4 Cards (Stats) */}
                <div className="grid grid-cols-4 gap-6 mb-10">
                  {[
                    { id: 'functional', label: state.summary_labels?.card1 || 'Functional', count: state.functional.length, sub: 'Extracted' },
                    { id: 'nfr', label: state.summary_labels?.card2 || 'Non-Functional', count: state.nfr.length, sub: 'Extracted' },
                    { id: 'stakeholders', label: state.summary_labels?.card3 || 'Stakeholders', count: state.stakeholders.length, sub: 'Identified' },
                    { id: 'decisions', label: state.summary_labels?.card4 || 'Decisions', count: state.decisions.length, sub: 'Recorded' },
                  ].map((card, i) => (
                    <div 
                      key={card.id}
                      onClick={() => handleCardClick('brd', card.id)} 
                      className={cn(
                        "bg-[#FBFBFA] p-6 rounded-xl border transition-all flex flex-col justify-between h-36 border-[#E5E7EB] cursor-pointer",
                        theme.hover,
                        "hover:shadow-[0_4px_12px_rgba(0,0,0,0.03)]"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-white border border-[#E5E7EB] text-gray-400 shadow-[0_1px_2px_rgba(0,0,0,0.04)]">{getCardIcon(i)}</div>
                        <span className="text-[13px] font-semibold text-[#37352F]">{card.label}</span>
                      </div>
                      <div className="flex flex-col mt-4">
                        <div className={cn("text-2xl font-bold tracking-tight transition-colors", theme.text)}>
                          {card.count}
                        </div>
                        <div className="text-[11px] font-medium text-gray-400 mt-0.5">{card.sub}</div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Main Dynamic View */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden min-h-[600px] relative">
                  <div className={cn("absolute top-0 left-0 right-0 h-1 z-10 transition-colors", theme.accent)}></div>
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={activeTab}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.15 }}
                      className="h-full bg-white"
                    >
                      {activeTab === 'brd' && <BRDOutput data={state} />}
                      {activeTab === 'analytics' && <Analytics data={state.analytics} />}
                      {activeTab === 'timeline' && <Timeline data={state.timeline} />}
                      {activeTab === 'priorities' && <Priorities priorities={state.priorities} functional={state.functional} />}
                      {activeTab === 'trace' && <SourceTrace data={state} sourceText={currentSourceText} />}
                      {activeTab === 'suggestions' && (
                        <div className="h-full overflow-y-auto px-10 py-10">
                          <SuggestionsPanel suggestions={state.suggestions} matchedBrds={state.matched_brds} isStandalone />
                        </div>
                      )}
                    </motion.div>
                  </AnimatePresence>
                </div>

                {/* Suggestions Section */}
                {activeTab === 'brd' && (
                  <SuggestionsPanel 
                    suggestions={state.suggestions} 
                    matchedBrds={state.matched_brds} 
                  />
                )}
              </div>

              {/* Right Input & Logs Column */}
              <div className="w-[400px] shrink-0 flex flex-col gap-6 sticky top-0 h-[calc(100vh-140px)]">
                <div className="bg-white p-6 rounded-2xl border border-gray-100/80 shadow-[0_2px_8px_rgba(0,0,0,0.02)] ring-1 ring-black/5 shrink-0 overflow-visible">
                  <h2 className="text-[13px] font-semibold text-gray-900 mb-5 flex items-center gap-2"><Lock className="w-4 h-4 text-gray-400" /> Start Extraction</h2>
                  <InputPanel onExtract={handleExtract} isLoading={state.isExtracting} />
                </div>

                <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-[0_4px_12px_rgba(0,0,0,0.01)] ring-1 ring-black/5 flex-1 flex flex-col min-h-[250px] overflow-hidden">
                  <h2 className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-6 flex items-center gap-2.5 shrink-0">
                    <Activity className="w-4 h-4 text-gray-400 select-none" /> 
                    <span>Agent Console</span>
                  </h2>
                  <div className="flex-1 overflow-hidden bg-[#FBFBFA]/80 rounded-2xl p-4 border border-gray-100/80 font-mono text-[14px] shadow-inner">
                    <AgentLog logs={state.logs} />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </main>

        <AnimatePresence>
          {state.error && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="fixed bottom-10 right-10 p-5 bg-white border-2 border-red-50 text-gray-900 rounded-3xl shadow-2xl z-[200] flex items-start gap-4 max-w-md ring-1 ring-black/5"
            >
              <div className="w-10 h-10 rounded-2xl bg-red-50 flex items-center justify-center shrink-0">
                <AlertCircle className="w-6 h-6 text-red-500" />
              </div>
              <div className="space-y-1">
                <h4 className="text-base font-black text-gray-900">System Warning</h4>
                <p className="text-xs font-bold text-gray-500 leading-normal">{state.error}</p>
                <div className="pt-2">
                  <button
                    onClick={() => setState(p => ({ ...p, error: null }))}
                    className="text-xs font-black text-red-500 bg-red-50 hover:bg-red-100 px-3 py-1.5 rounded-lg transition-colors"
                  >
                    Resolve Issues
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </SelectedReqProvider>
  );
}
