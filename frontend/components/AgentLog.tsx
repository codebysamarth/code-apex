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
    const isSuccess = log.includes('[SUCCESS]');
    const isError = log.includes('[ERROR]');
    const isDone = log.includes('[DONE]') || log.includes('[Done]');
    const isInit = log.includes('[Init]') || log.includes('[INIT]');

    if (isSuccess || isDone) return 'text-green-600 font-bold';
    if (isError) return 'text-red-500 font-bold';
    if (isInit) return 'text-blue-500 font-bold';
    return 'text-gray-500 font-semibold';
  };

  return (
    <div className="flex flex-col h-full bg-transparent overflow-hidden">
      <div className="flex-1 overflow-y-auto scrollbar-notion pr-2">
        <div className="space-y-1.5 pt-1">
          {logs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 opacity-50">
              <span className="text-2xl mb-2">📡</span>
              <p className="text-xs font-bold text-gray-400">Awaiting stream array...</p>
            </div>
          ) : (
            logs.map((log, i) => (
              <div key={i} className="flex items-start gap-2.5 py-1 px-1.5 rounded-lg hover:bg-gray-100 transition-colors">
                <span className="text-[10px] text-gray-300 font-bold mt-0.5 w-5 shrink-0 text-right select-none">
                  {(i + 1).toString().padStart(2, '0')}
                </span>
                <span className={cn("text-[11px] leading-relaxed font-mono tracking-tight", parseLog(log))}>
                  {log}
                </span>
              </div>
            ))
          )}
          <div ref={logEndRef} className="h-2" />
        </div>
      </div>

      <div className="mt-2 pt-2 border-t border-gray-200 flex items-center justify-between shrink-0">
        <span className="text-[10px] font-bold text-gray-400 tracking-wide">{logs.length} operations</span>
        <div className="flex items-center gap-1.5 bg-green-50 px-2 py-0.5 rounded-full border border-green-100">
          <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />
          <span className="text-[9px] font-bold text-green-700 uppercase tracking-widest">Live</span>
        </div>
      </div>
    </div>
  );
}
