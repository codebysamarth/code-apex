'use client';

import React from 'react';
import { PipelineStep } from '@/lib/types';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { Activity } from 'lucide-react';

interface AgentPipelineProps {
  steps: PipelineStep[];
}

export default function AgentPipeline({ steps }: AgentPipelineProps) {
  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center gap-2 border-b border-gray-200/40 pb-3.5">
        <Activity className="w-3.5 h-3.5 text-gray-400" />
        <h3 className="text-[11px] font-bold text-gray-400 uppercase tracking-[0.1em]">Pipeline Flow</h3>
      </div>

      <div className="flex flex-col gap-0 relative pl-1">
        {/* Track */}
        <div className="absolute left-[7px] top-4 bottom-4 w-[1px] bg-gray-200/60 z-0" />

        {steps.map((step) => (
          <div key={step.id} className={cn(
            "flex items-center gap-3.5 py-2.5 relative z-10 transition-opacity",
            step.status === 'idle' ? "opacity-30" : "opacity-100"
          )}>
            {/* Node */}
            <div className={cn(
              "w-3.5 h-3.5 rounded-full border flex items-center justify-center shrink-0 bg-white z-10 transition-all duration-300",
              step.status === 'done' ? "border-emerald-500 bg-emerald-50" :
                step.status === 'running' ? "border-indigo-500 bg-indigo-50 shadow-[0_0_8px_rgba(99,102,241,0.2)]" :
                  "border-gray-200 bg-white"
            )}>
              {step.status === 'done' && <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full" />}
              {step.status === 'running' && <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse" />}
            </div>

            <div className="flex items-center justify-between flex-1 min-w-0">
              <span className={cn(
                "text-[13px] transition-colors truncate",
                step.status === 'done' ? "text-gray-600 font-medium" :
                  step.status === 'running' ? "text-gray-900 font-semibold" : "text-gray-400 font-normal"
              )}>
                {step.label}
              </span>
              {step.timestamp && (
                <span className="text-[10px] text-gray-300 tabular-nums shrink-0 ml-2">{step.timestamp}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
