'use client';

import React, { useState, useEffect, useCallback } from 'react';
import InputPanel from '@/components/InputPanel';
import AgentPipeline from '@/components/AgentPipeline';
import AgentLog from '@/components/AgentLog';
import { BRDState, PipelineStep, ExtractionEvent, ModelStats } from '@/lib/types';
import { initialPipeline } from '@/lib/samples';
import { extractBRD, getHealth, getModelStats } from '@/lib/api';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, PieChart, Route, FileCheck, Target, SearchCheck, Calendar, RefreshCw, Box, Store, Users, Activity, Lock } from 'lucide-react';
import { SelectedReqProvider } from '@/context/SelectedReqContext';

import BRDOutput from '@/components/BRDOutput';
import Analytics from '@/components/Analytics';
import Timeline from '@/components/Timeline';
import Priorities from '@/components/Priorities';
import SourceTrace from '@/components/SourceTrace';
import ExportBRDButton from '@/components/ExportBRDButton';

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
    logs: [],
    isExtracting: false,
    error: null,
  });

  const [backendOffline, setBackendOffline] = useState(false);
  const [currentSourceText, setCurrentSourceText] = useState('');
  const [activeTab, setActiveTab] = useState('brd');
  const [modelStats, setModelStats] = useState<ModelStats[]>([]);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    const checkHealth = async () => {
      const health = await getHealth();
      setBackendOffline(health.status === 'offline');
    };
    checkHealth();
  }, []);

  const handleExtract = useCallback(async (text: string, sourceType: any = 'document') => {
    setCurrentSourceText(text);
    setState(prev => ({
      ...prev,
      isExtracting: true,
      error: null,
      logs: [`[${new Date().toLocaleTimeString()}] [system] Starting extraction: ${text.length} chars.`],
      pipeline: initialPipeline.map(s => ({ ...s, status: 'idle' as const }))
    }));

    await extractBRD({
      text,
      sourceType,
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
      onDone: (finalState: BRDState) => {
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

  useEffect(() => {
    if (activeTab === 'analytics') {
      getModelStats().then(setModelStats);
    }
  }, [activeTab]);

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
      <div className="flex h-screen bg-[#F6F8FA] font-sans antialiased text-[#111827] overflow-hidden">
        {/* Sidebar */}
        <aside className="w-[260px] bg-white flex flex-col justify-between h-full py-6 shadow-[1px_0_5px_rgba(0,0,0,0.02)] z-10 shrink-0">
          <div className="flex-1 flex flex-col overflow-hidden">
            <div className="px-6 flex items-center gap-2 mb-8 shrink-0">
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold text-lg shadow-sm">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 2L2 22h20L12 2z" fill="#fff" />
                </svg>
              </div>
              <span className="text-xl font-bold tracking-tight">ApexBRD</span>
            </div>

            <div className="px-4 shrink-0">
              <p className="px-2 text-[10px] font-bold text-gray-400 mb-2 uppercase tracking-widest leading-relaxed">Views</p>
              <nav className="space-y-1">
                <button onClick={() => setActiveTab('brd')} className={cn("w-full flex items-center gap-3 px-2 py-2.5 text-sm rounded-lg transition-colors", activeTab === 'brd' ? "bg-blue-50 text-blue-600 font-bold" : "text-gray-500 hover:bg-gray-50 font-semibold")}>
                  <FileCheck className={cn("w-4 h-4", activeTab === 'brd' ? "text-blue-500" : "text-gray-400")} /> Requirements
                </button>
                <button onClick={() => setActiveTab('analytics')} className={cn("w-full flex items-center gap-3 px-2 py-2.5 text-sm rounded-lg transition-colors", activeTab === 'analytics' ? "bg-blue-50 text-blue-600 font-bold" : "text-gray-500 hover:bg-gray-50 font-semibold")}>
                  <PieChart className={cn("w-4 h-4", activeTab === 'analytics' ? "text-blue-500" : "text-gray-400")} /> Analytics
                </button>
                <button onClick={() => setActiveTab('timeline')} className={cn("w-full flex items-center gap-3 px-2 py-2.5 text-sm rounded-lg transition-colors", activeTab === 'timeline' ? "bg-blue-50 text-blue-600 font-bold" : "text-gray-500 hover:bg-gray-50 font-semibold")}>
                  <Route className={cn("w-4 h-4", activeTab === 'timeline' ? "text-blue-500" : "text-gray-400")} /> Roadmap
                </button>
                <button onClick={() => setActiveTab('priorities')} className={cn("w-full flex items-center gap-3 px-2 py-2.5 text-sm rounded-lg transition-colors", activeTab === 'priorities' ? "bg-blue-50 text-blue-600 font-bold" : "text-gray-500 hover:bg-gray-50 font-semibold")}>
                  <Target className={cn("w-4 h-4", activeTab === 'priorities' ? "text-blue-500" : "text-gray-400")} /> Strategy
                </button>
                <button onClick={() => setActiveTab('trace')} className={cn("w-full flex items-center gap-3 px-2 py-2.5 text-sm rounded-lg transition-colors", activeTab === 'trace' ? "bg-blue-50 text-blue-600 font-bold" : "text-gray-500 hover:bg-gray-50 font-semibold")}>
                  <SearchCheck className={cn("w-4 h-4", activeTab === 'trace' ? "text-blue-500" : "text-gray-400")} /> Source Trace
                </button>
              </nav>
            </div>

            <div className="px-4 mt-8 flex-1 overflow-y-auto min-h-0 border-t border-gray-100 pt-6 mx-2 pb-4 scrollbar-notion">
              <p className="px-2 text-[10px] font-bold text-gray-400 mb-2 uppercase tracking-widest leading-relaxed">Pipeline Status</p>
              <div className="px-2 mt-2">
                <AgentPipeline steps={state.pipeline} />
              </div>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden px-10 py-8">
          {/* Health Banner */}
          {backendOffline && (
            <div className="bg-red-50 border border-red-200 p-2 rounded-lg mb-4 flex items-center justify-center gap-2 text-xs font-bold text-red-600 animate-pulse">
              <AlertCircle className="w-3.5 h-3.5" />
              BACKEND OFFLINE (http://localhost:8000)
            </div>
          )}

          {/* Header */}
          <header className="flex justify-between items-center mb-10 shrink-0">
            <div className="flex items-center gap-3">
            </div>
            <div className="flex items-center gap-4">
              <ExportBRDButton data={state} />
              <div className="flex items-center gap-2 text-sm font-bold text-gray-600 bg-white px-4 py-2 rounded-lg border border-gray-100 shadow-sm">
                <Calendar className="w-4 h-4 text-gray-400" /> {isMounted ? new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' }) : 'Loading Date...'}
              </div>
            </div>
          </header>

          <div className="flex-1 overflow-y-auto pb-20 scrollbar-notion pr-4">
            <div className="flex gap-8">
              <div className="flex-1 flex flex-col min-w-0">
                {/* Document Title Header */}
                <div className="flex justify-between items-center mb-8 pl-1">
                  <h1 className="text-[26px] font-black text-gray-900 tracking-tight">Requirement Extraction</h1>
                  <div className="flex items-center gap-3 text-[11px] font-bold text-gray-500 tracking-wider mt-2">
                    <span>Updated: {isMounted ? new Date().toLocaleTimeString() : '--:--:--'}</span>
                    <RefreshCw className={cn("w-3.5 h-3.5 cursor-pointer text-blue-500 stroke-[3]", state.isExtracting && "animate-spin")} />
                  </div>
                </div>

                {/* 4 Cards (Stats) */}
                <div className="grid grid-cols-4 gap-6 mb-8">
                  {/* Card 1 */}
                  <div onClick={() => handleCardClick('brd', 'functional')} className={cn("bg-white p-5 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] border transition-all flex flex-col justify-between h-36 border-gray-100 cursor-pointer hover:border-blue-200 hover:shadow-[0_4px_20px_rgba(0,0,0,0.06)]")}>
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-gray-100 text-gray-500"><Box className="w-[18px] h-[18px]" /></div>
                      <span className="text-sm font-bold text-gray-900">Functional</span>
                    </div>
                    <div className="flex gap-12 mt-4 px-1">
                      <div className="leading-tight">
                        <div className="text-2xl font-black text-gray-900">{state.functional.length}</div>
                        <div className="text-[11px] font-bold text-gray-400 mt-1">Extracted</div>
                      </div>
                    </div>
                  </div>

                  {/* Card 2 */}
                  <div onClick={() => handleCardClick('brd', 'nfr')} className="bg-white p-5 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] border border-gray-100 flex flex-col justify-between h-36 cursor-pointer hover:border-blue-200 hover:shadow-[0_4px_20px_rgba(0,0,0,0.06)] transition-all">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-gray-100 flex items-center justify-center"><Store className="w-[18px] h-[18px] text-gray-500" /></div>
                      <span className="text-sm font-bold text-gray-900">Non-Functional</span>
                    </div>
                    <div className="flex gap-12 mt-4 px-1">
                      <div className="leading-tight">
                        <div className="text-2xl font-black text-gray-900">{state.nfr.length}</div>
                        <div className="text-[11px] font-bold text-gray-400 mt-1">Extracted</div>
                      </div>
                    </div>
                  </div>

                  {/* Card 3 */}
                  <div onClick={() => handleCardClick('brd', 'stakeholders')} className="bg-white p-5 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] border border-gray-100 flex flex-col justify-between h-36 cursor-pointer hover:border-blue-200 hover:shadow-[0_4px_20px_rgba(0,0,0,0.06)] transition-all">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-gray-100 flex items-center justify-center"><Users className="w-[18px] h-[18px] text-gray-500" /></div>
                      <span className="text-sm font-bold text-gray-900">Stakeholders</span>
                    </div>
                    <div className="flex gap-12 mt-4 px-1">
                      <div className="leading-tight">
                        <div className="text-2xl font-black text-gray-900">{state.stakeholders.length}</div>
                        <div className="text-[11px] font-bold text-gray-400 mt-1">Identified</div>
                      </div>
                    </div>
                  </div>

                  {/* Card 4 */}
                  <div onClick={() => handleCardClick('brd', 'decisions')} className="bg-white p-5 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] border border-gray-100 flex flex-col justify-between h-36 cursor-pointer hover:border-blue-200 hover:shadow-[0_4px_20px_rgba(0,0,0,0.06)] transition-all">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-xl bg-gray-100 flex items-center justify-center"><Target className="w-[18px] h-[18px] text-gray-500" /></div>
                      <span className="text-sm font-bold text-gray-900">Decisions</span>
                    </div>
                    <div className="flex gap-12 mt-4 px-1">
                      <div className="leading-tight">
                        <div className="text-2xl font-black text-gray-900">{state.decisions.length}</div>
                        <div className="text-[11px] font-bold text-gray-400 mt-1">Recorded</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Main Dynamic View */}
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden min-h-[500px] relative">
                  {/* Active Border Hint */}
                  <div className="absolute top-0 left-0 right-0 h-1 bg-blue-500 z-10"></div>
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={activeTab}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.15 }}
                      className="h-full pt-2 bg-white"
                    >
                      {activeTab === 'brd' && <BRDOutput data={state} />}
                      {activeTab === 'analytics' && <Analytics data={state.analytics} />}
                      {activeTab === 'timeline' && <Timeline data={state.timeline} />}
                      {activeTab === 'priorities' && <Priorities priorities={state.priorities} functional={state.functional} />}
                      {activeTab === 'trace' && <SourceTrace data={state} sourceText={currentSourceText} />}
                    </motion.div>
                  </AnimatePresence>
                </div>
              </div>

              {/* Right Input & Logs Column */}
              <div className="w-[340px] shrink-0 flex flex-col gap-6 sticky top-0 h-[calc(100vh-140px)]">
                <div className="bg-white p-5 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] border border-gray-100 border-t-4 border-t-red-500 shrink-0">
                  <h2 className="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2"><Lock className="w-4 h-4 text-gray-400" /> Input Source</h2>
                  <div className="!shadow-none !border-none !p-0">
                    <InputPanel onExtract={handleExtract} isLoading={state.isExtracting} />
                  </div>
                </div>

                <div className="bg-white p-5 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] border border-gray-100 flex-1 flex flex-col min-h-0">
                  <h2 className="text-sm font-bold text-gray-900 mb-4 flex items-center gap-2 shrink-0"><Activity className="w-4 h-4 text-gray-400" /> System Logs</h2>
                  <div className="flex-1 overflow-hidden bg-gray-50 rounded-xl p-3 border border-gray-100">
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
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="fixed bottom-6 right-6 p-4 bg-white border border-[rgba(175,43,33,0.2)] rounded-2xl shadow-lg z-[200] flex items-start gap-3 max-w-sm"
            >
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <div className="space-y-1">
                <h4 className="text-sm font-bold text-red-500">Extraction Error</h4>
                <p className="text-xs font-semibold text-gray-500">{state.error}</p>
                <button
                  onClick={() => setState(p => ({ ...p, error: null }))}
                  className="mt-2 text-xs font-bold text-gray-400 hover:text-gray-900 transition-colors"
                >
                  Dismiss
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </SelectedReqProvider>
  );
}
