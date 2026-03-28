'use client';

import React from 'react';
import { BRDState } from '@/lib/types';
import { cn } from '@/lib/utils';
import { useSelectedReq } from '@/context/SelectedReqContext';
import { ListChecks, ShieldCheck, Users, Gavel, FileSearch, Info, Activity, Settings, BarChart3, ShieldAlert, Globe, Zap } from 'lucide-react';

interface BRDOutputProps {
  data: BRDState;
}

const priorityBadge: Record<string, string> = {
  high: 'bg-rose-50 text-rose-700 border-rose-100/50',
  medium: 'bg-amber-50 text-amber-700 border-amber-100/50',
  low: 'bg-emerald-50 text-emerald-700 border-emerald-100/50',
};

const moscowBadge: Record<string, string> = {
  Must: 'bg-rose-50 text-rose-700 border-rose-100/50',
  Should: 'bg-amber-50 text-amber-700 border-amber-100/50',
  Could: 'bg-sky-50 text-sky-700 border-sky-100/50',
  Wont: 'bg-slate-50 text-slate-500 border-slate-100/50',
};

const domainIcons: Record<string, any> = {
  software: { icon: '💻', label: 'Product Requirements Document', color: 'bg-[#f1f1ef]' },
  healthcare: { icon: '🏥', label: 'Clinical Systems Specification', color: 'bg-green-50' },
  mechanical: { icon: '⚙️', label: 'Mechanical Design Specification', color: 'bg-amber-50' },
  business: { icon: '📊', label: 'Business Strategy Roadmap', color: 'bg-blue-50' },
};

export default function BRDOutput({ data }: BRDOutputProps) {
  const { setSelectedReqId, setHoveredReqId, hoveredReqId, selectedReqId } = useSelectedReq();
  const domain = data.domain || 'software';
  const config = domainIcons[domain];

  if ((!data.functional || data.functional.length === 0) && !data.domain_data) {
    return (
      <div className="h-full min-h-[440px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-slate-50 text-slate-400 rounded-2xl flex items-center justify-center mb-5 border border-slate-100 shadow-sm">
          <FileSearch className="w-7 h-7" />
        </div>
        <h3 className="text-lg font-semibold text-slate-900 mb-1.5">No content generated</h3>
        <p className="text-[13px] font-normal text-slate-400">Process extraction to populate this space</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-16 md:px-20 font-sans antialiased text-[#37352F] transition-all">
      {/* Document Header */}
      <div className="mb-16 border-b border-gray-100 pb-12">
        <div className="flex items-center gap-3.5 mb-8">
          <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center text-xl border border-gray-100 shadow-sm", config.color)}>
            {config.icon}
          </div>
          <span className="text-[11px] font-bold uppercase tracking-[0.15em] text-gray-400/80">{domain} Mode</span>
        </div>
        <h1 className="text-[36px] font-bold tracking-tight text-[#37352F] leading-tight mb-8">
          {config.label}
        </h1>
        <div className="flex flex-wrap gap-4 mt-8">
          {data.domain_data?.compliance_check && (
            <div className="flex items-center gap-2.5 px-3 py-1.5 bg-white border border-gray-100 rounded-lg shadow-sm">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              <span className="text-[11px] font-semibold text-gray-500">Compliance: {data.domain_data.compliance_check.standard}</span>
              <span className={cn(
                "px-2 py-0.5 text-[9px] font-bold rounded-md border",
                data.domain_data.compliance_check.status === 'met' ? "bg-emerald-50 text-emerald-700 border-emerald-100/50" : "bg-amber-50 text-amber-700 border-amber-100/50"
              )}>
                {data.domain_data.compliance_check.status.toUpperCase()}
              </span>
            </div>
          )}
          {data.domain_data?.innovation_metrics && (
             <div className="flex items-center gap-2.5 px-3 py-1.5 bg-white border border-gray-100 rounded-lg shadow-sm">
                <Zap className="w-3.5 h-3.5 text-indigo-500" />
                <span className="text-[11px] font-semibold text-gray-500">Extraction Confidence: {Math.round(data.domain_data.innovation_metrics.domain_awareness_score * 100)}%</span>
             </div>
          )}
        </div>
      </div>

      {domain === 'software' ? (
        <>
          {/* Functional Requirements */}
          <section id="functional" className="mb-24">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3.5">
                <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center shadow-sm border border-rose-100/50">
                  <ListChecks className="w-[18px] h-[18px]" />
                </div>
                <h2 className="text-lg font-bold text-[#37352F]">Functional objectives</h2>
              </div>
              <span className="text-[11px] font-bold text-gray-400 bg-gray-50 px-3 py-1 rounded-full border border-gray-100/80">
                {data.functional.length} entries
              </span>
            </div>

            <div className="divide-y divide-gray-100 border-y border-gray-100">
              {data.functional.map((req) => (
                <div
                  key={req.id}
                  onClick={() => setSelectedReqId(req.id)}
                  onMouseEnter={() => setHoveredReqId(req.id)}
                  onMouseLeave={() => setHoveredReqId(null)}
                  className={cn(
                    "group relative py-8 px-5 cursor-pointer transition-all duration-200",
                    selectedReqId === req.id || hoveredReqId === req.id 
                      ? "bg-slate-50/50" 
                      : "bg-transparent hover:bg-slate-50/30"
                  )}
                >
                  <div className="flex items-start gap-8">
                    <span className="w-14 shrink-0 font-mono text-[11px] font-semibold text-gray-300 pt-1 pointer-events-none">
                      {req.id.includes('-') ? req.id : req.id.replace('FR', 'FR-')}
                    </span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-2.5">
                        <h3 className="text-base font-semibold text-[#111827] tracking-tight group-hover:text-black transition-colors">{req.title}</h3>
                        <div className="flex items-center gap-2">
                          {req.moscow && (
                            <span className={cn(
                              "px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded border",
                              moscowBadge[req.moscow] || 'bg-gray-50 text-gray-500 border-gray-100'
                            )}>
                              {req.moscow}
                            </span>
                          )}
                          <span className={cn(
                            "px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded border transition-opacity",
                            priorityBadge[req.priority.toLowerCase()] || 'bg-slate-50 text-slate-500 border-slate-100'
                          )}>
                            {req.priority}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-[11px] font-medium text-gray-400 mb-4">
                        <span className="flex items-center gap-1.5 tabular-nums">
                          <span className="w-1 h-1 rounded-full bg-emerald-500/60"></span>
                          Confidence: {Math.round(req.confidence * 100)}%
                        </span>
                        {req.sourceRef && (
                          <span className="opacity-60 tabular-nums">· Source Segment: {req.sourceRef}</span>
                        )}
                      </div>
                      {req.description && (
                        <p className="text-[15px] leading-relaxed text-gray-500 max-w-3xl font-normal">
                          {req.description}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Non-Functional Requirements */}
          <section id="nfr" className="mb-24">
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-3.5">
                <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center shadow-sm border border-emerald-100/50">
                  <ShieldCheck className="w-[18px] h-[18px]" />
                </div>
                <h2 className="text-lg font-bold text-[#37352F]">System constraints</h2>
              </div>
              <span className="text-[11px] font-bold text-gray-400 bg-gray-50 px-3 py-1 rounded-full border border-gray-100/80">
                {data.nfr.length} specifications
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {data.nfr.map((nfr) => (
                <div key={nfr.id} className="p-7 bg-white border border-gray-100 rounded-2xl hover:border-gray-200 transition-all shadow-[0_2px_8px_rgba(0,0,0,0.02)] group">
                  <div className="flex items-start gap-4 mb-5">
                    <span className="font-mono text-[10px] font-bold text-gray-300 bg-slate-50 border border-slate-100 px-2 py-0.5 rounded shrink-0 tabular-nums">
                      {nfr.id.includes('-') ? nfr.id : nfr.id.replace('NFR', 'NFR-')}
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600/80 bg-emerald-50 px-2 py-0.5 rounded-md">
                      {nfr.category}
                    </span>
                  </div>
                  <p className="text-sm font-semibold text-[#111827] leading-relaxed mb-6 group-hover:text-black transition-colors">{nfr.description}</p>
                  <div className="flex flex-wrap gap-2 mt-auto">
                    {nfr.constraints.map((c, i) => (
                      <span key={i} className="px-2.5 py-1 bg-slate-50 text-[10px] font-medium text-slate-500 rounded-md border border-slate-100">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Stakeholders & Decisions */}
          <section id="stakeholders" className="mb-24">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-20">
              {/* Stakeholders */}
              <div>
                <div className="flex items-center gap-3.5 mb-10">
                  <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shadow-sm border border-indigo-100/50">
                    <Users className="w-[18px] h-[18px]" />
                  </div>
                  <h2 className="text-lg font-bold text-[#37352F]">Stakeholders</h2>
                </div>
                <div className="space-y-4">
                  {data.stakeholders.map((s) => (
                    <div key={s.id} className="group p-4.5 bg-white border border-gray-100 rounded-xl hover:border-indigo-100 transition-all flex items-center gap-5 shadow-[0_1px_4px_rgba(0,0,0,0.01)]">
                      <div className="flex items-center justify-center min-w-[40px] w-auto h-9 px-3 font-mono text-[10px] font-bold text-indigo-500 bg-indigo-50/50 border border-indigo-100/40 rounded-lg shrink-0 whitespace-nowrap tabular-nums">
                        {s.id.includes('-') ? s.id : s.id.replace('S', 'S-')}
                      </div>
                      <div className="flex-1">
                        <p className="text-[14px] font-semibold text-[#111827] mb-0.5">{s.name}</p>
                        <p className="text-[12px] text-gray-400 font-medium">{s.role}</p>
                      </div>
                      <div className={cn(
                        "px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider border",
                        s.impact === 'High' ? "bg-rose-50 text-rose-600 border-rose-100/50" : "bg-slate-50 text-slate-400 border-slate-100/50"
                      )}>
                        {s.impact}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Decisions */}
              <div id="decisions">
                <div className="flex items-center gap-3.5 mb-10">
                  <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center shadow-sm border border-amber-100/50">
                    <Gavel className="w-[18px] h-[18px]" />
                  </div>
                  <h2 className="text-lg font-bold text-[#37352F]">Strategic decisions</h2>
                </div>
                <div className="space-y-8">
                  {data.decisions.map((d) => (
                    <div key={d.id} className="relative pl-7 py-0.5 border-l border-gray-100 group hover:border-amber-200 transition-all">
                      <div className="flex flex-col mb-2.5">
                        <span className="font-mono text-[10px] font-bold text-gray-300 mb-1 tabular-nums">
                          {d.id.includes('-') ? d.id : d.id.replace('D', 'D-')}
                        </span>
                        <h4 className="text-[15px] font-bold text-[#111827] tracking-tight">{d.decision}</h4>
                      </div>
                      <p className="text-[15px] text-gray-500 leading-relaxed font-normal">
                        <span className="font-semibold text-gray-900/60 uppercase text-[10px] tracking-wider mr-2">Rationale</span> {d.rationale}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </section>

          {/* Predictive Suggestions for Software */}
          {data.domain_data?.sections?.["Predictive Suggestions (FAISS RAG)"] && (
            <section id="suggestions" className="mb-24">
              <div className="flex items-center gap-3.5 mb-8">
                <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center shadow-sm border border-indigo-100/50">
                  <Zap className="w-[18px] h-[18px]" />
                </div>
                <h2 className="text-lg font-bold text-[#37352F]">Predictive Suggestions (FAISS RAG)</h2>
              </div>
              <div className="divide-y divide-gray-100 border-y border-gray-100">
                {data.domain_data.sections["Predictive Suggestions (FAISS RAG)"].map((item: any, idx: number) => (
                  <div key={idx} className="py-8 px-5 hover:bg-indigo-50/10 transition-colors">
                    <div className="flex items-center justify-between mb-3.5">
                      <h3 className="text-base font-semibold text-[#111827]">{item.title}</h3>
                      <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded border bg-indigo-50 text-indigo-700 border-indigo-100/50">
                        {item.priority}
                      </span>
                    </div>
                    <p className="text-[14px] leading-relaxed text-gray-500 font-normal max-w-2xl">
                      {item.description}
                    </p>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      ) : (
        <>
          {/* Dynamic Domain Sections */}
          {Object.entries(data.domain_data?.sections || {}).map(([sectionTitle, items]: [string, any]) => (
             <section key={sectionTitle} className="mb-24">
                <div className="flex items-center justify-between mb-8 group">
                  <div className="flex items-center gap-3.5">
                    <div className="w-8 h-8 rounded-lg bg-slate-50 text-slate-400 flex items-center justify-center shadow-sm border border-slate-100/80">
                      <ListChecks className="w-4 h-4" />
                    </div>
                    <h2 className="text-lg font-bold text-[#37352F]">{sectionTitle}</h2>
                  </div>
                </div>

                <div className="divide-y divide-gray-100 border-y border-gray-100">
                  {Array.isArray(items) && items.map((item: any, idx) => (
                    <div key={idx} className="py-8 px-5 hover:bg-slate-50/30 transition-colors">
                       <div className="flex items-start gap-8">
                          <div className="flex-1">
                             <div className="flex items-center justify-between mb-3.5">
                                <h3 className="text-base font-semibold text-[#111827]">{item.title || item.name || item.objective}</h3>
                                {item.priority && (
                                   <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider rounded border bg-slate-50 text-slate-500 border-slate-100/80">
                                      {item.priority}
                                   </span>
                                )}
                             </div>
                             <p className="text-[14px] leading-relaxed text-gray-500 font-normal max-w-2xl">
                                {item.description || item.requirement || item.specification || JSON.stringify(item)}
                             </p>
                             {item.mitigation && (
                                <div className="mt-5 p-4 bg-rose-50/30 border border-rose-100/50 rounded-xl flex gap-3 items-start">
                                   <ShieldAlert className="w-3.5 h-3.5 text-rose-500 mt-0.5" />
                                   <span className="text-[11px] font-semibold text-rose-700/80 uppercase tracking-wide">Mitigation: {item.mitigation}</span>
                                </div>
                             )}
                          </div>
                       </div>
                    </div>
                  ))}
                </div>
             </section>
          ))}

          {/* Domain Specific Scores */}
          <section className="mb-24">
             <div className="flex items-center justify-between mb-10">
                <div className="flex items-center gap-3.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-500 flex items-center justify-center shadow-sm border border-indigo-100/50">
                  <BarChart3 className="w-[18px] h-[18px]" />
                </div>
                <h2 className="text-lg font-bold text-[#37352F]">Performance & Industrial impact</h2>
              </div>
             </div>
             <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {Object.entries(data.domain_data?.domain_scores || {}).map(([key, score]: [string, any]) => (
                   <div key={key} className="p-6 bg-[#FBFBFA] border border-gray-100 rounded-2xl shadow-[0_1px_3px_rgba(0,0,0,0.01)] transition-all hover:bg-white hover:shadow-[0_4px_12px_rgba(0,0,0,0.02)]">
                      <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-gray-400 mb-3">{key.replace(/_/g, ' ')}</p>
                      <div className="flex items-end gap-1 mb-4">
                         <span className="text-2xl font-bold tracking-tight text-gray-900 tabular-nums">{Math.round((score.value || score) * 100)}%</span>
                      </div>
                      <p className="text-[12px] text-gray-400 font-normal leading-relaxed">{score.rationale || 'Industrial validity score based on domain context'}</p>
                   </div>
                ))}
             </div>
          </section>
        </>
      )}

      {data.domain_data?.innovation_metrics?.conflict_detection && (
         <div className="mb-24 p-8 bg-[#FBFBFA] border border-amber-200/40 rounded-2xl flex gap-5 items-start shadow-sm shadow-amber-500/5">
            <div className="w-10 h-10 rounded-xl bg-white border border-amber-100 flex items-center justify-center shrink-0 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
               <Info className="w-5 h-5 text-amber-500" />
            </div>
            <div>
               <h4 className="text-[15px] font-bold text-amber-900 mb-1.5">Architectural Conflict Detection</h4>
               <p className="text-[14px] text-amber-800/80 leading-relaxed font-normal">
                  {data.domain_data.innovation_metrics.conflict_detection}
               </p>
            </div>
         </div>
      )}

      <footer className="h-60 border-t border-gray-100 flex flex-col items-center justify-center gap-4">
        <div className="w-8 h-1 bg-gray-100 rounded-full" />
        <p className="text-[10px] font-bold text-gray-300 uppercase tracking-[0.4em]">End of document</p>
      </footer>
    </div>
  );
}
