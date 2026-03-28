'use client';

import React from 'react';
import { TimelineItem } from '@/lib/types';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { Activity, CalendarDays, Route } from 'lucide-react';

interface TimelineProps {
  data: TimelineItem[];
}

export default function Timeline({ data }: TimelineProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-full min-h-[440px] flex flex-col items-center justify-center">
        <div className="w-16 h-16 bg-slate-50 text-slate-400 rounded-2xl flex items-center justify-center mb-5 border border-slate-100 shadow-sm">
          <CalendarDays className="w-7 h-7" />
        </div>
        <h3 className="text-lg font-semibold text-slate-900 mb-1.5">No roadmap available</h3>
        <p className="text-[13px] font-normal text-slate-400">Extract requirements to generate timeline.</p>
      </div>
    );
  }

  return (
    <div className="p-10 max-w-4xl mx-auto space-y-10 pb-32 font-sans antialiased">
      <motion.div 
        initial={{ opacity: 0, x: -10 }} 
        animate={{ opacity: 1, x: 0 }} 
        className="flex items-center gap-2.5 pb-4 border-b border-gray-100"
      >
        <Route className="w-4 h-4 text-gray-400" />
        <h3 className="text-[13px] font-bold text-gray-900 uppercase tracking-widest leading-relaxed">Implementation Roadmap</h3>
      </motion.div>

      <div className="relative pl-1">
        {/* Timeline Track */}
        <div className="absolute left-[7px] top-6 bottom-0 w-[1px] bg-gray-200/40" />

        <motion.div 
          className="space-y-10"
          variants={{
            show: { transition: { staggerChildren: 0.1 } }
          }}
          initial="hidden"
          animate="show"
        >
          {data.map((item, index) => (
            <motion.div 
              key={index} 
              variants={{
                hidden: { opacity: 0, y: 15 },
                show: { opacity: 1, y: 0 }
              }}
              className="flex items-start gap-8 relative group"
            >
              <div className="w-3.5 h-3.5 rounded-full border border-indigo-500 bg-white z-10 shrink-0 mt-1.5 group-hover:scale-110 transition-transform shadow-[0_0_0_4px_rgba(255,255,255,1),0_0_12px_rgba(99,102,241,0.1)]" />

              <div className="flex-1 p-7 bg-white border border-gray-100/80 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.02)] transition-all hover:border-indigo-100/50 hover:shadow-[0_4px_20px_rgba(0,0,0,0.04)] ring-1 ring-black/5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2.5">
                    <span className="px-2.5 py-1 rounded-md text-[10px] font-black uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-100/30">
                      {item.phase}
                    </span>
                    {index === 0 && (
                      <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider bg-emerald-50 text-emerald-600 border border-emerald-100/50">
                        <Activity className="w-2.5 h-2.5" /> Starting Point
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 text-[11px] text-gray-400 font-semibold tabular-nums">
                    <CalendarDays className="w-3 h-3 opacity-60" />
                    {item.duration}
                  </div>
                </div>
                <h4 className="text-base font-bold text-[#111827] mb-3 leading-tight tracking-tight group-hover:text-indigo-600 transition-colors">
                  {item.activity}
                </h4>
                <div className="flex items-start gap-3 p-3.5 bg-gray-50/50 rounded-xl border border-gray-100/40">
                  <div className="w-5 h-5 rounded-lg bg-white flex items-center justify-center border border-gray-100 shadow-sm shrink-0">
                    <span className="text-[10px]">📦</span>
                  </div>
                  <p className="text-[13px] text-gray-500 leading-relaxed font-medium italic opacity-85">
                    {item.deliverable}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </div>
  );
}
