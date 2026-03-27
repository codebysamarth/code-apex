'use client';

import React from 'react';
import { PriorityScore, FunctionalReq } from '@/lib/types';
import { cn } from '@/lib/utils';

import { Target } from 'lucide-react';

interface PrioritiesProps {
  priorities: PriorityScore[];
  functional: FunctionalReq[];
}

export default function Priorities({ priorities, functional }: PrioritiesProps) {
  const hasMoscow = functional.some(f => f.moscow);

  if (!priorities || priorities.length === 0) {
    return (
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mb-4 shadow-[0_4px_12px_rgba(59,130,246,0.1)]">
          <Target className="w-8 h-8" />
        </div>
        <h3 className="text-[17px] font-black text-gray-900 mb-1">No strategy available</h3>
        <p className="text-[13px] font-bold text-gray-400">Extract requirements to generate strategy.</p>
      </div>
    );
  }

  if (!hasMoscow) {
    return (
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-gray-50 text-gray-400 rounded-full flex items-center justify-center mb-4 border border-gray-100 opacity-50">
          <Target className="w-8 h-8" />
        </div>
        <h3 className="text-[17px] font-black text-gray-900 mb-1">MoSCoW prioritization not available for this dataset</h3>
        <p className="text-[13px] font-bold text-gray-400 italic opacity-75">Please use an input with clearer priority language (must, should, could).</p>
      </div>
    );
  }

  const moscowGroups = ['Must', 'Should', 'Could', 'Wont'] as const;

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-12 pb-32">
      <div className="flex items-center gap-2 pb-2 border-b border-[rgba(55,53,47,0.06)] mb-2">
        <span className="text-[14px]">🎯</span>
        <h3 className="text-[14px] font-semibold text-[rgba(55,53,47,1)]">MoSCoW Prioritization Strategy</h3>
      </div>

      <div className="space-y-12">
        {moscowGroups.map(group => {
          const groupReqs = functional.filter(f => f.moscow === group);
          if (groupReqs.length === 0) return null;

          return (
            <section key={group} className="space-y-4">
              <div className="flex items-center gap-3">
                <span className={cn(
                  "px-2 py-0.5 text-[10px] font-black uppercase tracking-wider rounded border",
                  group === 'Must' ? 'bg-red-50 text-red-700 border-red-100' :
                  group === 'Should' ? 'bg-amber-50 text-amber-700 border-amber-100' :
                  group === 'Could' ? 'bg-yellow-50 text-yellow-700 border-yellow-100' :
                  'bg-gray-50 text-gray-500 border-gray-100'
                )}>
                  {group}
                </span>
                <span className="text-[11px] font-bold text-gray-400">{groupReqs.length} items</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {groupReqs.map(req => {
                  const p = priorities.find(ps => ps.requirementId === req.id);
                  if (!p) return null;

                  return (
                    <div key={req.id} className="p-4 bg-white border border-[rgba(55,53,47,0.09)] rounded-lg hover:bg-[rgba(55,53,47,0.02)] transition-colors">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="text-[11px] font-mono text-[#2383e2]">{req.id}</span>
                        <h4 className="text-[13px] font-semibold text-[rgba(55,53,47,0.85)] truncate">{req.title}</h4>
                      </div>

                      <div className="space-y-3">
                        {[
                          { label: 'Impact', val: p.impact, color: 'bg-[#2383e2]' },
                          { label: 'Effort', val: p.effort, color: 'bg-[#e3e2e0]' },
                          { label: 'Urgency', val: p.urgency, color: 'bg-[#fdecc8]' },
                        ].map((m) => (
                          <div key={m.label} className="space-y-1">
                            <div className="flex justify-between text-[11px] text-[rgba(55,53,47,0.5)]">
                              <span className="capitalize">{m.label}</span>
                              <span className="font-mono">{Number(m.val).toFixed(2)}/10</span>
                            </div>
                            <div className="h-[6px] bg-[#f7f7f5] rounded-full overflow-hidden border border-[rgba(55,53,47,0.06)]">
                              <div className={cn("h-full rounded-full transition-all duration-500", m.color)} style={{ width: `${m.val * 10}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="mt-3 pt-3 border-t border-[rgba(55,53,47,0.06)] flex items-center justify-between">
                        <span className="text-[11px] text-[rgba(55,53,47,0.35)]">Total score</span>
                        <span className="text-[16px] font-bold text-[rgba(55,53,47,1)]">{Number(p.total).toFixed(2)}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>

      {/* Strategy Callout — Notion style */}
      <div className="p-4 bg-[#fbfbfa] border border-[rgba(55,53,47,0.09)] rounded-lg flex items-start gap-3">
        <span className="text-[18px]">💡</span>
        <div>
          <h4 className="text-[13px] font-semibold text-[rgba(55,53,47,0.85)] mb-1">Rollout strategy</h4>
          <p className="text-[13px] text-[rgba(55,53,47,0.5)] leading-relaxed">
            Phase 1 focuses on <strong>Must-Have</strong> requirements with high urgency. Phase 2 should address <strong>Should-Have</strong> items that maximize total value vs effort score.
          </p>
        </div>
      </div>
    </div>
  );
}
