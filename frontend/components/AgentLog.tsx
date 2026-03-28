'use client';

import React, { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';

interface AgentLogProps {
  logs: string[];
}

export default function AgentLog({ logs }: AgentLogProps) {
  const logEndRef = useRef<HTMLDivElement>(null);
  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [logs]);

  const parseLog = (log: string) => {
    const isSuccess = log.includes('completed successfully') || log.includes('[SUCCESS]');
    const isError = log.includes('[error]') || log.includes('[ERROR]');
    const isAgent = log.includes('engaged') || log.includes('starting');
    const isSystem = log.includes('[system]');

    if (isSuccess) return 'text-emerald-600 font-semibold bg-emerald-50/50 rounded-lg px-2 py-0.5 border border-emerald-100/40 inline-block';
    if (isError) return 'text-rose-500 font-semibold bg-rose-50/50 rounded-lg px-2 py-0.5 border border-rose-100/40 inline-block';
    if (isAgent) return 'text-indigo-600 font-bold tracking-tight';
    if (isSystem) return 'text-slate-400 font-medium italic opacity-80';
    
    return 'text-slate-600 font-normal';
  };

  return (
    <div className="flex flex-col h-full bg-transparent overflow-hidden">
      <div className="flex-1 overflow-y-auto scrollbar-minimal pr-1">
        <div className="space-y-2 pt-1">
          {logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-6 opacity-40">
              <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center mb-3">
                <span className="text-lg">📡</span>
              </div>
              <p className="text-[11px] font-medium text-slate-400">Awaiting agent stream...</p>
            </div>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="flex items-start gap-5 py-1.5 px-2.5 rounded-xl transition-all hover:bg-white hover:shadow-[0_2px_8px_rgba(0,0,0,0.02)] border border-transparent hover:border-gray-100 group">
                <span className="text-[11px] text-slate-300 font-medium mt-1 w-7 shrink-0 text-right select-none tabular-nums opacity-60 group-hover:opacity-100 transition-opacity">
                  {i + 1}
                </span>
                <span className={cn("text-[14px] leading-relaxed font-mono tracking-tight", parseLog(log))}>
                  {log}
                </span>
              </div>
            ))
          )}
          <div ref={logEndRef} className="h-4" />
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between shrink-0">
        <span className="text-[10px] font-medium text-slate-400 tracking-wide">{logs.length} operations</span>
        <div className="flex items-center gap-1.5 bg-emerald-50/50 px-2 py-0.5 rounded-full border border-emerald-100/50">
          <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse opacity-70" />
          <span className="text-[9px] font-semibold text-emerald-700 uppercase tracking-widest">Live</span>
        </div>
      </div>
    </div>
  );
}
