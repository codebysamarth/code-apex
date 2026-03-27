'use client';

import React from 'react';
import { PipelineStep } from '@/lib/types';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';

interface AgentPipelineProps {
  steps: PipelineStep[];
}

export default function AgentPipeline({ steps }: AgentPipelineProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 border-b border-[rgba(55,53,47,0.06)] pb-3">
        <span className="text-[14px]">⚙️</span>
        <h3 className="text-[13px] font-semibold text-[rgba(55,53,47,1)]">Pipeline</h3>
      </div>

      <div className="flex flex-col gap-0 relative">
        {/* Track */}
        <div className="absolute left-[7px] top-4 bottom-4 w-[1.5px] bg-[rgba(55,53,47,0.06)] z-0" />

        {steps.map((step) => (
          <div key={step.id} className={cn(
            "flex items-center gap-3 py-2 relative z-10 transition-opacity",
            step.status === 'idle' ? "opacity-35" : "opacity-100"
          )}>
            {/* Node */}
            <div className={cn(
              "w-[15px] h-[15px] rounded-full border-2 flex items-center justify-center shrink-0 bg-white z-10 transition-all",
              step.status === 'done' ? "border-[#1c7636] bg-[#dbeddb]" :
                step.status === 'running' ? "border-[#2383e2] bg-[#d3e5ef]" :
                  "border-[rgba(55,53,47,0.16)] bg-white"
            )}>
              {step.status === 'done' && <span className="text-[8px]">✓</span>}
              {step.status === 'running' && <div className="w-[5px] h-[5px] bg-[#2383e2] rounded-full animate-pulse" />}
            </div>

            <div className="flex items-center justify-between flex-1 min-w-0">
              <span className={cn(
                "text-[13px] font-medium transition-colors truncate",
                step.status === 'done' ? "text-[rgba(55,53,47,0.85)]" :
                  step.status === 'running' ? "text-[rgba(55,53,47,1)]" : "text-[rgba(55,53,47,0.45)]"
              )}>
                {step.label}
              </span>
              {step.timestamp && (
                <span className="text-[11px] text-[rgba(55,53,47,0.35)] shrink-0 ml-2">{step.timestamp}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
