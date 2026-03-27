'use client';

import React from 'react';
import { TimelineItem } from '@/lib/types';

import { CalendarDays } from 'lucide-react';

interface TimelineProps {
  data: TimelineItem[];
}

export default function Timeline({ data }: TimelineProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-full min-h-[400px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mb-4 shadow-[0_4px_12px_rgba(59,130,246,0.1)]">
          <CalendarDays className="w-8 h-8" />
        </div>
        <h3 className="text-[17px] font-black text-gray-900 mb-1">No roadmap available</h3>
        <p className="text-[13px] font-bold text-gray-400">Extract requirements to generate timeline.</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-8 pb-32">
      <div className="flex items-center gap-2 pb-2 border-b border-[rgba(55,53,47,0.06)]">
        <span className="text-[14px]">🗓️</span>
        <h3 className="text-[14px] font-semibold text-[rgba(55,53,47,1)]">Implementation roadmap</h3>
      </div>

      <div className="relative">
        {/* Timeline Track */}
        <div className="absolute left-[7px] top-6 bottom-0 w-[1.5px] bg-[rgba(55,53,47,0.08)]" />

        <div className="space-y-6">
          {data.map((item, index) => (
            <div key={index} className="flex items-start gap-5 relative group">
              <div className="w-[15px] h-[15px] rounded-full border-2 border-[#2383e2] bg-white z-10 shrink-0 mt-1 group-hover:bg-[#d3e5ef] transition-colors" />

              <div className="flex-1 p-4 bg-white border border-[rgba(55,53,47,0.09)] rounded-lg hover:bg-[rgba(55,53,47,0.02)] transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-[#d3e5ef] text-[#30789b]">{item.phase}</span>
                  <span className="text-[11px] text-[rgba(55,53,47,0.35)] font-mono">{item.duration}</span>
                </div>
                <h4 className="text-[14px] font-semibold text-[rgba(55,53,47,0.85)] mb-1">{item.activity}</h4>
                <p className="text-[13px] text-[rgba(55,53,47,0.5)] leading-relaxed">{item.deliverable}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
