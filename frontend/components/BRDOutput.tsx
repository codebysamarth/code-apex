'use client';

import React from 'react';
import { BRDState } from '@/lib/types';
import { cn } from '@/lib/utils';
import { useSelectedReq } from '@/context/SelectedReqContext';
import { ListChecks, ShieldCheck, Users, Gavel, FileSearch, Info } from 'lucide-react';

interface BRDOutputProps {
  data: BRDState;
}

const priorityBadge: Record<string, string> = {
  high: 'bg-[#ffe2dd] text-[#af2b21]',
  medium: 'bg-[#fdecc8] text-[#685519]',
  low: 'bg-[#dbeddb] text-[#1c7636]',
};

const moscowBadge: Record<string, string> = {
  Must: 'bg-red-50 text-red-700 border-red-100',
  Should: 'bg-amber-50 text-amber-700 border-amber-100',
  Could: 'bg-yellow-50 text-yellow-700 border-yellow-100',
  Wont: 'bg-gray-50 text-gray-500 border-gray-100',
};

export default function BRDOutput({ data }: BRDOutputProps) {
  const { setSelectedReqId, setHoveredReqId, hoveredReqId, selectedReqId } = useSelectedReq();

  if (!data.functional || data.functional.length === 0) {
    return (
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mb-4 border border-blue-100">
          <FileSearch className="w-8 h-8" />
        </div>
        <h3 className="text-[17px] font-black text-gray-900 mb-1">No requirements extracted</h3>
        <p className="text-[13px] font-bold text-gray-400">Paste a document and click Extract to begin</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12 md:px-16 font-['Inter'] transition-all">
      {/* Document Header */}
      <div className="mb-14 border-b border-[#E9E9E7] pb-10">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-[#F1F1EF] flex items-center justify-center text-xl shadow-[inset_0_1px_2px_rgba(0,0,0,0.05)] border border-[#E9E9E7]">📄</div>
          <span className="text-xs font-bold uppercase tracking-[0.2em] text-[#AFAFAF]">Document</span>
        </div>
        <h1 className="text-[42px] font-extrabold tracking-tight text-[#37352F] leading-[1.1] mb-6">
          Product Requirements Document
        </h1>
        <p className="text-[#787774] text-[17px] leading-relaxed max-w-2xl font-medium opacity-90">
          Automated extraction of business logic and functional specifications for the ApexBRD intelligence layer.
        </p>
      </div>

      {/* Functional Requirements */}
      <section id="functional" className="mb-20">
        <div className="flex items-center justify-between mb-8 group">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-[#ffe2dd] text-[#af2b21] flex items-center justify-center shadow-sm border border-red-100">
              <ListChecks className="w-[18px] h-[18px]" />
            </div>
            <h2 className="text-[17px] font-bold text-[#37352F]">Functional requirements</h2>
          </div>
          <span className="text-[11px] font-bold text-[#787774] bg-[#f0edea] px-2.5 py-1 rounded-full border border-[#E9E9E7]">
            {data.functional.length} entries
          </span>
        </div>

        <div className="divide-y divide-[#E9E9E7] border-y border-[#E9E9E7]">
          {data.functional.map((req) => (
            <div
              key={req.id}
              onClick={() => setSelectedReqId(req.id)}
              onMouseEnter={() => setHoveredReqId(req.id)}
              onMouseLeave={() => setHoveredReqId(null)}
              className={cn(
                "group relative py-6 px-4 cursor-pointer transition-all duration-200",
                selectedReqId === req.id || hoveredReqId === req.id 
                  ? "bg-[#F7F7F5]" 
                  : "bg-transparent hover:bg-[#F7F7F5]/50"
              )}
            >
              <div className="flex items-start gap-6">
                <span className="w-14 shrink-0 font-mono text-[13px] font-bold text-[#AFAFAF] pt-0.5">
                  {req.id.includes('-') ? req.id : req.id.replace('FR', 'FR-')}
                </span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-[16px] font-bold text-[#37352F] tracking-tight group-hover:text-black transition-colors">{req.title}</h3>
                    <div className="flex items-center gap-2">
                      {req.moscow && (
                        <span className={cn(
                          "px-2 py-0.5 text-[9px] font-black uppercase tracking-wider rounded border",
                          moscowBadge[req.moscow] || 'bg-gray-50 text-gray-500 border-gray-100'
                        )}>
                          {req.moscow}
                        </span>
                      )}
                      <span className={cn(
                        "px-2 py-0.5 text-[10px] font-black uppercase tracking-wider rounded border transition-opacity",
                        priorityBadge[req.priority.toLowerCase()] || 'bg-[#f0edea] text-[#49473f]',
                        "border-black/5"
                      )}>
                        {req.priority}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-[12px] font-semibold text-[#787774] mb-3">
                    <span className="flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                      Confidence: {Math.round(req.confidence * 100)}%
                    </span>
                    {req.sourceRef && (
                      <span className="opacity-50">· Source: {req.sourceRef}</span>
                    )}
                  </div>
                  {req.description && (
                    <p className="text-[14px] leading-relaxed text-[#787774] max-w-2xl font-normal">
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
      <section id="nfr" className="mb-20">
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-md bg-[#dbeddb] text-[#1c7636] flex items-center justify-center shadow-sm border border-green-100">
              <ShieldCheck className="w-[18px] h-[18px]" />
            </div>
            <h2 className="text-[17px] font-bold text-[#37352F]">Non-functional requirements</h2>
          </div>
          <span className="text-[11px] font-bold text-[#787774] bg-[#f0edea] px-2.5 py-1 rounded-full border border-[#E9E9E7]">
            {data.nfr.length} specifications
          </span>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.nfr.map((nfr) => (
            <div key={nfr.id} className="p-6 bg-white border border-[#E9E9E7] rounded-xl hover:border-[#37352F]/20 transition-all shadow-[0_1px_3px_rgba(0,0,0,0.02)] group">
              <div className="flex items-start gap-4 mb-4">
                <span className="font-mono text-[12px] font-bold text-[#AFAFAF] bg-[#F7F7F5] border border-[#E9E9E7] px-1.5 py-0.5 rounded shrink-0">
                  {nfr.id.includes('-') ? nfr.id : nfr.id.replace('NFR', 'NFR-')}
                </span>
                <span className="text-[11px] font-black uppercase tracking-wider text-[#1c7636] bg-[#dbeddb]/50 px-2 py-0.5 rounded">
                  {nfr.category}
                </span>
              </div>
              <p className="text-[15px] font-bold text-[#37352F] leading-snug mb-4 group-hover:text-black transition-colors">{nfr.description}</p>
              <div className="flex flex-wrap gap-1.5 mt-auto">
                {nfr.constraints.map((c, i) => (
                  <span key={i} className="px-2 py-0.5 bg-[#F7F7F5] text-[10px] font-bold text-[#787774] rounded border border-[#E9E9E7]">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Stakeholders & Decisions */}
      <section id="stakeholders" className="mb-20">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
          {/* Stakeholders */}
          <div>
            <div className="flex items-center gap-3 mb-8">
              <div className="w-8 h-8 rounded-md bg-[#d3e5ef] text-[#30789b] flex items-center justify-center shadow-sm border border-blue-100">
                <Users className="w-[18px] h-[18px]" />
              </div>
              <h2 className="text-[17px] font-bold text-[#37352F]">Stakeholders</h2>
            </div>
            <div className="space-y-4">
              {data.stakeholders.map((s) => (
                <div key={s.id} className="group p-4 bg-white border border-[#E9E9E7] rounded-lg hover:border-[#30789b]/30 transition-all flex items-center gap-5">
                  <div className="flex items-center justify-center min-w-[40px] w-auto h-10 px-2 font-mono text-[11px] font-bold text-[#30789b] bg-[#d3e5ef]/40 border border-[#d3e5ef] rounded-md shrink-0 whitespace-nowrap">
                    {s.id.includes('-') ? s.id : s.id.replace('S', 'S-')}
                  </div>
                  <div className="flex-1">
                    <p className="text-[14px] font-bold text-[#37352F] mb-0.5">{s.name}</p>
                    <p className="text-[12px] text-[#787774] font-medium opacity-80">{s.role}</p>
                  </div>
                  <div className={cn(
                    "px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-tighter border",
                    s.impact === 'High' ? "bg-red-50 text-red-600 border-red-100" : "bg-gray-50 text-gray-500 border-gray-100"
                  )}>
                    {s.impact}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Decisions */}
          <div id="decisions">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-8 h-8 rounded-md bg-[#fdecc8] text-[#685519] flex items-center justify-center shadow-sm border border-yellow-100">
                <Gavel className="w-[18px] h-[18px]" />
              </div>
              <h2 className="text-[17px] font-bold text-[#37352F]">Decisions</h2>
            </div>
            <div className="space-y-6">
              {data.decisions.map((d) => (
                <div key={d.id} className="relative pl-6 py-1 border-l-2 border-[#E9E9E7] group hover:border-[#685519]/40 transition-all">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="font-mono text-[12px] font-bold text-[#AFAFAF] h-4 leading-none">
                      {d.id.includes('-') ? d.id : d.id.replace('D', 'D-')}
                    </span>
                    <h4 className="text-[15px] font-extrabold text-[#37352F] tracking-tight">{d.decision}</h4>
                  </div>
                  <p className="text-[13px] text-[#787774] leading-relaxed pl-7">
                    <span className="font-bold text-[#37352F]/60">Rationale:</span> {d.rationale}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <footer className="h-40 border-t border-[#E9E9E7] flex items-center justify-center">
        <p className="text-[12px] font-bold text-[#AFAFAF] uppercase tracking-[0.3em]">End of document</p>
      </footer>
    </div>
  );
}
